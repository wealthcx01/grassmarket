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
)
from bcap_contracts.common import NonScoreState
from bcap_contracts.registry import Registry
from bcap_contracts.uncertainty import UncertaintyModel

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


def _complete_inputs(document: AssessmentDocument, registry: Registry) -> AssessmentInputs:
    """Build full engine inputs from a partial document: unrated subcomponents and unobserved
    metrics become Not Assessed (first-class); powers are taken as given (scoreability ensures 7).
    """
    from bcap_contracts.assessments import SubcomponentRating

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
    return LiveScore(
        scoreable=True,
        v=_band(unc.v_band),
        b=_band(unc.b_band),
        p=_band(unc.p_band),
        l_index=_band(unc.l_band),
        module_qm={k: _band(v) for k, v in unc.module_qm.items()},
        overall_uncertainty=unc.overall_uncertainty,
        subcomponents_assessed=assessed,
        subcomponents_total=total,
        coverage=coverage,
        engine_version=engine_version,
        methodology_version=methodology_version,
        coefficient_version=coefficient_version,
        uncertainty_version=uncertainty_version,
    )
