"""Live-score service — completes a partial document to engine inputs and scores what it can.

A wizard document is partial. The engine requires exact registry coverage, so this service:
- fills every unrated subcomponent and unobserved metric with **Not Assessed** (first-class, never
  zero-filled — the D9 defence);
- checks scoreability (L needs a rated subcomponent in a core module; B needs a metric; P needs all
  7 powers) and reports what is still blocking rather than raising a 500;
- when scoreable, runs the deterministic engine + Monte Carlo and returns V/L/B/P bands with the
  ADR-0008 `modelled` flags, so the client labels B/P honestly.
"""

from __future__ import annotations

from dataclasses import dataclass

from bcap_contracts.assessments import (
    AssessmentDocument,
    CoefficientSet,
    IndexBand,
    LiveScore,
    MetricEntry,
    PowerEntry,
    SubcomponentRating,
)
from bcap_contracts.common import NonScoreState, StrengthRating
from bcap_contracts.registry import Registry
from bcap_contracts.uncertainty import UncertaintyModel
from bcap_contracts.value import ScenarioComparison

from grassmarket.atlas import (
    ENGINE_VERSION,
    AssessmentInputs,
    AtlasResult,
    MetricObservation,
    PowerObservation,
    run_monte_carlo,
    score,
)
from grassmarket.atlas.montecarlo import Band, SupportsRandom, UncertaintyResult
from grassmarket.value import evaluate_scenario, prioritise_upgrades

LIVE_DRAWS = 400  # modest draw count for a responsive on-demand live panel

# Core modules the L min-term ranges over (the draft critical-for-L set, GRS-0003).
_CRITICAL_MODULES_FOR_L = ("APP_SERVER", "BACKOFFICE", "OEMS")


@dataclass(frozen=True)
class ScoreArtifacts:
    """Everything a finalised scoring run needs: the completed engine inputs, the deterministic
    result, and the Monte Carlo bands."""

    inputs: AssessmentInputs
    result: AtlasResult
    uncertainty: UncertaintyResult


def scoreability_blockers(document: AssessmentDocument, registry: Registry) -> list[str]:
    """What is still needed before V can be computed. Empty ⟹ scoreable."""
    blockers: list[str] = []

    doc_powers = {p.power_key for p in document.powers}
    missing_powers = registry.power_keys() - doc_powers
    if missing_powers:
        blockers.append(
            f"Rate all 7 Strategic Powers (missing: {', '.join(sorted(missing_powers))})."
        )

    if not any(
        m.raw is not None for m in document.metrics if m.metric_key in registry.metric_keys()
    ):
        blockers.append("Enter at least one business metric.")

    core_subs = {
        s.key for k in _CRITICAL_MODULES_FOR_L for s in registry.require_module(k).subcomponents
    }
    if not any(
        r.level is not None and r.subcomponent_key in core_subs for r in document.subcomponents
    ):
        blockers.append(
            "Rate at least one subcomponent in a core module (App Server, Back Office, or OEMS)."
        )
    return blockers


def consensus_blockers(document: AssessmentDocument) -> list[str]:
    """What dual-rating governance still blocks finalisation (Methodology §9). Every ASSESSED
    subcomponent (level set) must carry a resolved consensus: two raters and either agreement
    (`consensus=True`) or a documented dissent. A solo-rated subcomponent is a draft, never a
    deliverable — so a document with one blocks the whole finalisation, loudly. Not Assessed / Not
    Applicable subcomponents carry no rating and are exempt."""
    blockers: list[str] = []
    for r in document.subcomponents:
        if r.level is None:
            continue
        if len(set(r.rater_ids)) < 2:
            blockers.append(
                f"{r.module_key}/{r.subcomponent_key} is solo-rated — Methodology §9 requires two "
                f"independent raters and a resolved consensus."
            )
        elif not r.consensus and r.dissent_note is None:
            blockers.append(
                f"{r.module_key}/{r.subcomponent_key} has neither a recorded consensus nor a "
                f"documented dissent."
            )
    return blockers


def module_rating_errors(
    module_key: str, ratings: tuple[SubcomponentRating, ...], registry: Registry
) -> list[str]:
    """Validate a rater's (or a consensus) rating set against the registry: the module must exist
    and every subcomponent must belong to it. Fail loud — an unknown key is never scored around."""
    from bcap_contracts.registry import RegistryError

    try:
        module = registry.require_module(module_key)
    except RegistryError as exc:
        return [str(exc)]
    valid = {s.key for s in module.subcomponents}
    return [
        f"Subcomponent {r.subcomponent_key!r} is not part of module {module_key!r}."
        for r in ratings
        if r.subcomponent_key not in valid
    ]


def _complete_inputs(document: AssessmentDocument, registry: Registry) -> AssessmentInputs:
    """Build full engine inputs from a partial document: unrated subcomponents and unobserved
    metrics become Not Assessed (first-class); powers are taken as given (scoreability ensures 7).
    """
    doc_subs = {r.subcomponent_key: r for r in document.subcomponents}
    subs: list[SubcomponentRating] = []
    for module in registry.modules:
        for sub in module.subcomponents:
            if sub.key in doc_subs:
                subs.append(doc_subs[sub.key])
            else:
                subs.append(
                    SubcomponentRating(
                        module_key=module.key,
                        subcomponent_key=sub.key,
                        state=NonScoreState.NOT_ASSESSED,
                    )
                )

    doc_metrics = {m.metric_key: m for m in document.metrics}
    metrics = [
        _to_metric_obs(doc_metrics[k]) if k in doc_metrics else _not_assessed_metric(k)
        for k in sorted(registry.metric_keys())
    ]
    doc_powers = {p.power_key: p for p in document.powers}
    powers = [_to_power_obs(doc_powers[k]) for k in sorted(registry.power_keys())]
    return AssessmentInputs(subcomponents=tuple(subs), metrics=tuple(metrics), powers=tuple(powers))


def _to_metric_obs(m: MetricEntry) -> MetricObservation:
    return MetricObservation(
        metric_key=m.metric_key, raw=m.raw, state=m.state, confidence=m.confidence
    )


def _not_assessed_metric(key: str) -> MetricObservation:
    return MetricObservation(metric_key=key, state=NonScoreState.NOT_ASSESSED)


def _to_power_obs(p: PowerEntry) -> PowerObservation:
    return PowerObservation(
        power_key=p.power_key,
        benefit=p.benefit,
        barrier=p.barrier,
        benefit_grade=p.benefit_grade,
        barrier_grade=p.barrier_grade,
    )


def _coverage(document: AssessmentDocument, registry: Registry) -> tuple[int, int, float | None]:
    """(assessed, total, coverage) — assessed subcomponents over APPLICABLE ones (Not Applicable
    excluded), matching the §7 coverage notion. Not Assessed counts as applicable-but-unassessed."""
    total = len(registry.all_subcomponent_keys())
    doc = {
        r.subcomponent_key: r
        for r in document.subcomponents
        if r.subcomponent_key in registry.all_subcomponent_keys()
    }
    assessed = sum(1 for r in doc.values() if r.level is not None)
    not_applicable = sum(1 for r in doc.values() if r.state == NonScoreState.NOT_APPLICABLE)
    applicable = total - not_applicable
    coverage = round(assessed / applicable, 6) if applicable else None
    return assessed, total, coverage


def compute_score(
    document: AssessmentDocument,
    coefficients: CoefficientSet,
    registry: Registry,
    model: UncertaintyModel,
    rng: SupportsRandom,
    *,
    draws: int = LIVE_DRAWS,
) -> ScoreArtifacts:
    """Score a document assumed scoreable (caller checks `scoreability_blockers`). Wraps the engine
    + Monte Carlo; the completed inputs are what a finalised run persists."""
    inputs = _complete_inputs(document, registry)
    result = score(inputs, coefficients, registry)
    uncertainty = run_monte_carlo(inputs, coefficients, registry, model, rng, draws=draws)
    return ScoreArtifacts(inputs=inputs, result=result, uncertainty=uncertainty)


def _band(band: Band) -> IndexBand:
    return IndexBand(p10=band.p10, p50=band.p50, p90=band.p90, modelled=band.modelled)


def _triad_rating(rating: str | None) -> StrengthRating | None:
    """A triad dimension with no assessed source is Not Assessed (None on the wire), never coerced
    into the StrengthRating.NONE moat floor (D9)."""
    return StrengthRating(rating) if rating is not None else None


def live_score(
    document: AssessmentDocument,
    coefficients: CoefficientSet,
    registry: Registry,
    model: UncertaintyModel,
    rng: SupportsRandom,
    *,
    draws: int = LIVE_DRAWS,
) -> LiveScore:
    """The live panel output for the current (possibly partial) document."""
    assessed, total, coverage = _coverage(document, registry)
    engine_version = ENGINE_VERSION
    methodology_version = coefficients.methodology_version
    coefficient_version = coefficients.version
    uncertainty_version = model.version

    blockers = scoreability_blockers(document, registry)
    if blockers:
        return LiveScore(
            scoreable=False,
            blocking=tuple(blockers),
            subcomponents_assessed=assessed,
            subcomponents_total=total,
            coverage=coverage,
            engine_version=engine_version,
            methodology_version=methodology_version,
            coefficient_version=coefficient_version,
            uncertainty_version=uncertainty_version,
        )

    art = compute_score(document, coefficients, registry, model, rng, draws=draws)
    unc = art.uncertainty
    triad = art.result.triad
    return LiveScore(
        scoreable=True,
        v=_band(unc.v_band),
        b=_band(unc.b_band),
        p=_band(unc.p_band),
        l_index=_band(unc.l_band),
        module_qm={k: _band(v) for k, v in unc.module_qm.items()},
        triad_economic=_triad_rating(triad.economic_value.rating),
        triad_perceived=_triad_rating(triad.perceived_value.rating),
        triad_defence=_triad_rating(triad.defence_value.rating),
        overall_uncertainty=unc.overall_uncertainty,
        subcomponents_assessed=assessed,
        subcomponents_total=total,
        coverage=coverage,
        engine_version=engine_version,
        methodology_version=methodology_version,
        coefficient_version=coefficient_version,
        uncertainty_version=uncertainty_version,
    )


def evaluate_scenarios(
    baseline: AssessmentDocument,
    named_scenarios: list[tuple[str, AssessmentDocument]],
    coefficients: CoefficientSet,
    registry: Registry,
) -> ScenarioComparison:
    """Compare candidate upgrade scenarios against the baseline by full re-scoring — ΔV → the
    Upgrade Priority Index (score domain only, ADR-0002). The baseline must be scoreable; each
    scenario is completed to engine inputs the same way (unrated → Not Assessed) and evaluated."""
    blockers = scoreability_blockers(baseline, registry)
    if blockers:
        return ScenarioComparison(scoreable=False, blocking=tuple(blockers))

    # Each scenario is a full what-if document completed to engine inputs the same way — but
    # _complete_inputs indexes powers directly, so an unscoreable scenario (e.g. a missing power)
    # would raise rather than report. Check scoreability first and surface it, never a 500.
    scenario_blockers = [
        f"Scenario '{name}': {b}"
        for name, doc in named_scenarios
        for b in scoreability_blockers(doc, registry)
    ]
    if scenario_blockers:
        return ScenarioComparison(scoreable=False, blocking=tuple(scenario_blockers))

    baseline_inputs = _complete_inputs(baseline, registry)
    scenario_inputs = [(name, _complete_inputs(doc, registry)) for name, doc in named_scenarios]
    results = tuple(
        evaluate_scenario(name, baseline_inputs, inputs, coefficients, registry)
        for name, inputs in scenario_inputs
    )
    priority = tuple(prioritise_upgrades(baseline_inputs, scenario_inputs, coefficients, registry))
    baseline_v = score(baseline_inputs, coefficients, registry).composite.v_index
    return ScenarioComparison(
        scoreable=True, baseline_v=baseline_v, results=results, priority_index=priority
    )
