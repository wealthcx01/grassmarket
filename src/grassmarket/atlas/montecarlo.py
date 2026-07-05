"""The uncertainty engine — Monte Carlo over the deterministic kernel (Methodology v1.1 §7).

Monte Carlo **wraps** `score()`; it never reimplements scoring. Each draw perturbs the *inputs*
(subcomponent maturity levels, by evidence grade) and runs the untouched deterministic engine, so
the point estimate and every band come from one code path.

Randomness is the first in the codebase, and it is contained: the RNG is **injected and seeded**
(a `random.Random` or a numpy `Generator` — both satisfy the `.random()` protocol), never module
-global and never time-seeded. Same seed + same draws ⇒ byte-identical bands, so the determinism
guarantee that protects the golden master is preserved. Draws consume the RNG in a fixed registry
order for exact reproducibility.

§7 mechanism (this ticket): the input distribution is evidence-grade-driven, which the methodology
defines only for subcomponents. Metric and power inputs carry no evidence grade, so B and P are held
at their point values (reported as degenerate bands) until their own input-uncertainty models —
financial measurement error, committee confidence — are added. V and L carry real ranges.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Protocol

from bcap_contracts.assessments import CoefficientSet, SubcomponentRating
from bcap_contracts.common import (
    EvidenceGrade,
    MaturityLevel,
    NonScoreState,
    Score,
    UncertaintyRating,
    WeightMethod,
)
from bcap_contracts.provenance import WeightProvenanceRecord
from bcap_contracts.registry import Registry
from bcap_contracts.uncertainty import UncertaintyModel
from pydantic import BaseModel, ConfigDict

from grassmarket.atlas.engine import score
from grassmarket.atlas.inputs import AssessmentInputs
from grassmarket.atlas.results import AtlasResult

DEFAULT_DRAWS = 2000

# Maturity levels ordered by rank (1..4); index i holds the level of rank i+1.
_LEVELS_BY_RANK: tuple[MaturityLevel, ...] = (
    MaturityLevel.BASIC,
    MaturityLevel.DEVELOPING,
    MaturityLevel.ADVANCED,
    MaturityLevel.FRONTIER,
)

# Assessment Uncertainty Rating bands on the confidence score (coverage × evidence factor). These
# are §7 reporting cut-offs — a documented discretisation, not elicited weights. Rater agreement is
# a THIRD confidence input (§7) that arrives with dual-rating in a later loop; noted, not yet used.
_RATING_BANDS: tuple[tuple[float, UncertaintyRating], ...] = (
    (0.75, UncertaintyRating.LOW),
    (0.50, UncertaintyRating.MEDIUM),
    (0.25, UncertaintyRating.HIGH),
)


class SupportsRandom(Protocol):
    """The minimal RNG surface Monte Carlo needs — `random()` → float in [0, 1). Satisfied by both
    `random.Random` and numpy's `Generator`, so either can be injected (seeded) by the caller."""

    def random(self) -> float: ...


# --- Result types -----------------------------------------------------------------------


class Band(BaseModel):
    """A P10/P50/P90 uncertainty band (Methodology §7). Degenerate (all equal) when the input has
    no modelled uncertainty."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    p10: Score
    p50: Score
    p90: Score


class TornadoEntry(BaseModel):
    """One input's swing on V across its uncertainty support (others held at point)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    subcomponent_key: str
    swing: float  # V(high support) − V(low support)
    v_low: Score
    v_high: Score


class WeightStabilityInterval(BaseModel):
    """The V range as θ/α move over a documented neighbourhood — does the headline survive weight
    movement (Methodology §7). A narrow interval ⇒ the conclusion is robust to the weights."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    v_point: Score
    v_low: Score
    v_high: Score


class UncertaintyResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    draws: int
    v_band: Band
    l_band: Band
    b_band: Band
    p_band: Band
    module_qm: dict[str, Band]
    overall_uncertainty: UncertaintyRating
    module_uncertainty: dict[str, UncertaintyRating]
    tornado: tuple[TornadoEntry, ...]
    weight_stability: WeightStabilityInterval


# --- Draft coefficients (uncertainty widths) --------------------------------------------


def draft_v1_uncertainty_model() -> UncertaintyModel:
    """The v1 DRAFT evidence-grade widths — documented placeholders, NOT client-usable. Ratified by
    the same elicitation as θ/α (§6). E4 tight (2% leaves the point level) → E1 wide (50%, so an
    E1 rating genuinely spans the adjacent level)."""
    return UncertaintyModel(
        version="v1-draft-pending-elicitation",
        methodology_version="1.1",
        evidence_spreads={"E1": 0.50, "E2": 0.25, "E3": 0.10, "E4": 0.02},
        client_usable=False,
        provenance=WeightProvenanceRecord(
            set_by="draft-pending-elicitation",
            set_on=date(2026, 7, 5),
            method=WeightMethod.DIRECT,
            dispersion="n/a — draft placeholder widths",
            review_due=date(2026, 12, 31),
            notes="Draft §7 input-distribution widths pending elicitation; NOT client-usable.",
        ),
    )


# --- Public entry point -----------------------------------------------------------------


def run_monte_carlo(
    inputs: AssessmentInputs,
    coefficients: CoefficientSet,
    registry: Registry,
    model: UncertaintyModel,
    rng: SupportsRandom,
    *,
    draws: int = DEFAULT_DRAWS,
) -> UncertaintyResult:
    """Run `draws` Monte Carlo iterations over `score()` and summarise the §7 outputs."""
    if draws < 1:
        raise ValueError(f"draws must be ≥ 1, got {draws}.")
    coefficients.validate_against(registry)  # fail loud once, not per draw
    point = score(inputs, coefficients, registry)
    subs_by_key = {r.subcomponent_key: r for r in inputs.subcomponents}

    v_s: list[float] = []
    l_s: list[float] = []
    b_s: list[float] = []
    p_s: list[float] = []
    qm_s: dict[str, list[float]] = {m.key: [] for m in registry.modules}

    for _ in range(draws):
        drawn = _perturb(inputs, subs_by_key, registry, model, rng)
        res = score(drawn, coefficients, registry)
        v_s.append(res.composite.v_index)
        l_s.append(res.composite.l_index)
        b_s.append(res.composite.b_index)
        p_s.append(res.composite.p_index)
        for mr in res.modules:
            if mr.q_m is not None:
                qm_s[mr.key].append(mr.q_m)

    module_qm = {k: _band(v) for k, v in qm_s.items() if v}
    overall_rating, module_ratings = _uncertainty_ratings(point, subs_by_key, registry)
    return UncertaintyResult(
        draws=draws,
        v_band=_band(v_s),
        l_band=_band(l_s),
        b_band=_band(b_s),
        p_band=_band(p_s),
        module_qm=module_qm,
        overall_uncertainty=overall_rating,
        module_uncertainty=module_ratings,
        tornado=_tornado(inputs, coefficients, registry, subs_by_key),
        weight_stability=_weight_stability(inputs, coefficients, registry, point.composite.v_index),
    )


# --- Sampling ---------------------------------------------------------------------------


def _perturb(
    inputs: AssessmentInputs,
    subs_by_key: dict[str, SubcomponentRating],
    registry: Registry,
    model: UncertaintyModel,
    rng: SupportsRandom,
) -> AssessmentInputs:
    """Draw one perturbed assessment. Subcomponents are sampled in registry order (fixed RNG
    consumption). Metrics and powers pass through unchanged (no §7 distribution in v1)."""
    new_subs: list[SubcomponentRating] = []
    for module in registry.modules:
        for sub in module.subcomponents:
            rating = subs_by_key[sub.key]
            if rating.state == NonScoreState.NOT_APPLICABLE:
                new_subs.append(rating)  # out of scope in every draw — never sampled
                continue
            if rating.state == NonScoreState.NOT_ASSESSED:
                # Missing evidence → maximal ignorance: uniform over all four levels, and INCLUDED
                # this draw so the unknown widens the band (§7). E1 grade is a placeholder; only the
                # continuous outputs are read from a draw.
                level = _uniform_level(rng)
                new_subs.append(
                    SubcomponentRating(
                        module_key=module.key,
                        subcomponent_key=sub.key,
                        level=level,
                        evidence_grade=EvidenceGrade.E1_SELF_REPORTED,
                    )
                )
                continue
            assert rating.level is not None and rating.evidence_grade is not None
            level = _sample_level(rng, rating.level, rating.evidence_grade, model)
            new_subs.append(
                SubcomponentRating(
                    module_key=module.key,
                    subcomponent_key=sub.key,
                    level=level,
                    evidence_grade=rating.evidence_grade,
                )
            )
    return AssessmentInputs(
        subcomponents=tuple(new_subs), metrics=inputs.metrics, powers=inputs.powers
    )


def _sample_level(
    rng: SupportsRandom, level: MaturityLevel, grade: EvidenceGrade, model: UncertaintyModel
) -> MaturityLevel:
    """Adjacent-level categorical: `1 − spread` on the point level, the rest on the adjacent
    level(s). Endpoints (Basic/Frontier) put all adjacent mass on their single neighbour."""
    spread = model.evidence_spreads[grade.value]
    rank = level.rank  # 1..4
    lower = rank - 1 >= 1
    upper = rank + 1 <= 4
    weighted: list[tuple[MaturityLevel, float]] = [(level, 1.0 - spread)]
    if lower and upper:
        weighted.append((_LEVELS_BY_RANK[rank - 2], spread / 2))
        weighted.append((_LEVELS_BY_RANK[rank], spread / 2))
    elif lower:
        weighted.append((_LEVELS_BY_RANK[rank - 2], spread))
    else:  # upper only (Basic)
        weighted.append((_LEVELS_BY_RANK[rank], spread))
    return _weighted_choice(rng, weighted)


def _uniform_level(rng: SupportsRandom) -> MaturityLevel:
    return _LEVELS_BY_RANK[min(3, int(rng.random() * 4))]


def _weighted_choice(
    rng: SupportsRandom, weighted: list[tuple[MaturityLevel, float]]
) -> MaturityLevel:
    total = math.fsum(w for _, w in weighted)
    x = rng.random() * total
    cumulative = 0.0
    for level, weight in weighted:
        cumulative += weight
        if x < cumulative:
            return level
    return weighted[-1][0]  # pragma: no cover — floating-point tail


# --- Percentiles & bands ----------------------------------------------------------------


def _percentile(sorted_values: list[float], q: float) -> float:
    """Linear-interpolation percentile (numpy's default 'linear' method), q in [0, 1]."""
    if not sorted_values:  # pragma: no cover — guarded by callers
        raise ValueError("percentile of an empty sample")
    if len(sorted_values) == 1:
        return sorted_values[0]
    idx = (len(sorted_values) - 1) * q
    low = math.floor(idx)
    high = math.ceil(idx)
    if low == high:
        return sorted_values[low]
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * (idx - low)


def _band(values: list[float]) -> Band:
    ordered = sorted(values)
    return Band(
        p10=round(_percentile(ordered, 0.10), 6),
        p50=round(_percentile(ordered, 0.50), 6),
        p90=round(_percentile(ordered, 0.90), 6),
    )


# --- Assessment Uncertainty Rating ------------------------------------------------------


def _uncertainty_ratings(
    point: AtlasResult, subs_by_key: dict[str, SubcomponentRating], registry: Registry
) -> tuple[UncertaintyRating, dict[str, UncertaintyRating]]:
    """Confidence = coverage × evidence factor (mean assessed evidence rank / 4), per module and
    overall. Higher confidence → lower uncertainty. (Rater agreement is a later §7 input.)"""
    module_ratings: dict[str, UncertaintyRating] = {}
    all_ranks: list[int] = []
    total_assessed = total_applicable = 0

    for module in registry.modules:
        mr = next(m for m in point.modules if m.key == module.key)
        assessed_ranks: list[int] = []
        for s in module.subcomponents:
            rating = subs_by_key[s.key]
            if rating.level is not None and rating.evidence_grade is not None:
                assessed_ranks.append(rating.evidence_grade.rank)
        all_ranks.extend(assessed_ranks)
        total_assessed += mr.n_assessed
        total_applicable += mr.n_applicable
        coverage = mr.coverage if mr.coverage is not None else 0.0
        module_ratings[module.key] = _rating(_confidence(coverage, assessed_ranks))

    overall_coverage = total_assessed / total_applicable if total_applicable else 0.0
    return _rating(_confidence(overall_coverage, all_ranks)), module_ratings


def _confidence(coverage: float, evidence_ranks: list[int]) -> float:
    if not evidence_ranks:
        return 0.0  # nothing assessed → no confidence → Very High uncertainty
    evidence_factor = (sum(evidence_ranks) / len(evidence_ranks)) / 4.0  # E1..E4 → 0.25..1.0
    return coverage * evidence_factor


def _rating(confidence: float) -> UncertaintyRating:
    for threshold, rating in _RATING_BANDS:
        if confidence >= threshold:
            return rating
    return UncertaintyRating.VERY_HIGH


# --- Tornado (deterministic) ------------------------------------------------------------


def _tornado(
    inputs: AssessmentInputs,
    coefficients: CoefficientSet,
    registry: Registry,
    subs_by_key: dict[str, SubcomponentRating],
) -> tuple[TornadoEntry, ...]:
    """One-at-a-time swing of V across each input's uncertainty support (others at point): assessed
    subcomponents move ±1 level; a Not-Assessed subcomponent spans the whole scale (Basic↔Frontier),
    so a missing assessment surfaces as high leverage. Ranked by |swing| descending."""
    entries: list[TornadoEntry] = []
    for module in registry.modules:
        for sub in module.subcomponents:
            rating = subs_by_key[sub.key]
            if rating.state == NonScoreState.NOT_APPLICABLE:
                continue  # out of scope — no swing
            if rating.state == NonScoreState.NOT_ASSESSED:
                low, high = MaturityLevel.BASIC, MaturityLevel.FRONTIER
                grade = EvidenceGrade.E1_SELF_REPORTED
            else:
                assert rating.level is not None and rating.evidence_grade is not None
                rank = rating.level.rank
                low = _LEVELS_BY_RANK[max(1, rank - 1) - 1]
                high = _LEVELS_BY_RANK[min(4, rank + 1) - 1]
                grade = rating.evidence_grade
            v_low = _score_with_override(
                inputs, coefficients, subs_by_key, registry, sub.key, low, grade, module.key
            )
            v_high = _score_with_override(
                inputs, coefficients, subs_by_key, registry, sub.key, high, grade, module.key
            )
            entries.append(
                TornadoEntry(
                    subcomponent_key=sub.key,
                    swing=round(v_high - v_low, 6),
                    v_low=round(v_low, 6),
                    v_high=round(v_high, 6),
                )
            )
    entries.sort(key=lambda e: abs(e.swing), reverse=True)
    return tuple(entries)


def _score_with_override(
    inputs: AssessmentInputs,
    coefficients: CoefficientSet,
    subs_by_key: dict[str, SubcomponentRating],
    registry: Registry,
    target_key: str,
    level: MaturityLevel,
    grade: EvidenceGrade,
    target_module: str,
) -> float:
    """Score with a single subcomponent forced to `level` (others at their point values)."""
    new_subs: list[SubcomponentRating] = []
    for module in registry.modules:
        for sub in module.subcomponents:
            if sub.key == target_key:
                new_subs.append(
                    SubcomponentRating(
                        module_key=target_module,
                        subcomponent_key=target_key,
                        level=level,
                        evidence_grade=grade,
                    )
                )
            else:
                new_subs.append(subs_by_key[sub.key])
    drawn = AssessmentInputs(
        subcomponents=tuple(new_subs), metrics=inputs.metrics, powers=inputs.powers
    )
    return score(drawn, coefficients, registry).composite.v_index


# --- Weight stability -------------------------------------------------------------------

# A documented θ/α neighbourhood for the stability sweep (draft). Real stability intervals come from
# the swing-elicitation panel (§6); this modest neighbourhood shows whether the headline V survives
# plausible weight movement. Each θ triple sums to 1 (enforced by CoefficientSet on the base set).
_THETA_VARIANTS: tuple[tuple[float, float, float], ...] = (
    (0.30, 0.30, 0.40),  # base
    (0.35, 0.30, 0.35),
    (0.30, 0.35, 0.35),
    (0.25, 0.25, 0.50),
    (0.35, 0.35, 0.30),
    (0.40, 0.30, 0.30),
)
_ALPHA_L_VARIANTS: tuple[float, ...] = (0.6, 0.7, 0.8)


def _weight_stability(
    inputs: AssessmentInputs,
    coefficients: CoefficientSet,
    registry: Registry,
    v_point: float,
) -> WeightStabilityInterval:
    """Recompute V (point inputs) as θ and α_L move over the documented neighbourhood; report the
    interval. `model_copy` reuses every validated key family — only the weight values change."""
    vs: list[float] = []
    for theta_b, theta_p, theta_l in _THETA_VARIANTS:
        for alpha_l in _ALPHA_L_VARIANTS:
            variant = coefficients.model_copy(
                update={
                    "theta_b": theta_b,
                    "theta_p": theta_p,
                    "theta_l": theta_l,
                    "alpha_l": alpha_l,
                }
            )
            vs.append(score(inputs, variant, registry).composite.v_index)
    return WeightStabilityInterval(
        v_point=round(v_point, 6), v_low=round(min(vs), 6), v_high=round(max(vs), 6)
    )
