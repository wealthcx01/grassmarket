"""The deterministic ATLAS scoring engine (Methodology v1.1 §5).

Pure, contracts-typed, fail-loud. No database, no I/O, no clock, no randomness — given the same
inputs, coefficients, and registry it returns the same result, forever. This is the product the
GRS-0003 reference script (``scripts/build_golden_master.py``) specified; the golden-master test
proves the two agree to the last decimal.

Fail-loud everywhere (the D1–D7 defence):
- inputs must cover the registry EXACTLY (a missing/extra key refuses to score);
- the coefficient set is validated against the registry before any arithmetic;
- every coefficient lookup is bracket access — a missing weight, group weight, or strength encoding
  raises, it never defaults;
- Not Assessed contributes to nothing and taints coverage/gate; Not Applicable renormalises weights;
  a fully-unassessed module's q_m is None, never 0.0 (D9).
"""

from __future__ import annotations

from bcap_contracts.assessments import CoefficientSet, SubcomponentRating
from bcap_contracts.common import EvidenceGrade, MaturityLevel, NonScoreState
from bcap_contracts.registry import MetricDef, Registry

from grassmarket.atlas.inputs import AssessmentInputs, MetricObservation, PowerObservation
from grassmarket.atlas.results import (
    AtlasResult,
    BusinessResult,
    CompositeResult,
    LResult,
    MetricRow,
    ModuleResult,
    PowerRow,
    PowersResult,
    SubcomponentRow,
    TriadDimensionResult,
    TriadResult,
)

ENGINE_VERSION = "0.1.0"

# The rating-gate band for each ordinal rank (Methodology v1.1 §5.2a).
_RANK_BAND = {1: "Basic", 2: "Developing", 3: "Advanced", 4: "Frontier"}

# §2 construct definitions — which inputs feed each triad dimension. Named here (not magic) because
# §2 fixes them: Economic = B's scale + unit-economics signal; Perceived = the Benefit side of these
# two powers; Defence = the Barrier aggregate across all 7 powers.
_ECONOMIC_GROUPS = ("scale", "unit_economics")
_PERCEIVED_POWERS = ("BRANDING", "SWITCHING_COSTS")


def _round(x: float) -> float:
    return round(x, 6)


def score(
    inputs: AssessmentInputs,
    coefficients: CoefficientSet,
    registry: Registry,
    *,
    engine_version: str = ENGINE_VERSION,
) -> AtlasResult:
    """Score one complete assessment end-to-end (two-track, Methodology v1.1 §5)."""
    coefficients.validate_against(registry)
    _assert_inputs_cover_registry(inputs, registry)

    subs_by_key = {r.subcomponent_key: r for r in inputs.subcomponents}
    metrics_by_key = {m.metric_key: m for m in inputs.metrics}
    powers_by_key = {p.power_key: p for p in inputs.powers}

    module_results, q_by_module = _score_modules(registry, coefficients, subs_by_key)
    l_result, l_value = _score_l(registry, coefficients, q_by_module)
    business, group_means_raw, b_value = _score_business(registry, coefficients, metrics_by_key)
    powers_result, p_value = _score_powers(registry, coefficients, powers_by_key)
    triad = _score_triad(registry, coefficients, powers_by_key, group_means_raw)

    v_value = (
        coefficients.theta_b * b_value
        + coefficients.theta_p * p_value
        + (coefficients.theta_l * l_value)
    )
    v_stored = _round(v_value)
    composite = CompositeResult(
        b_index=_round(b_value),
        p_index=_round(p_value),
        l_index=_round(l_value),
        v_index=v_stored,
    )
    return AtlasResult(
        engine_version=engine_version,
        methodology_version=coefficients.methodology_version,
        coefficient_version=coefficients.version,
        modules=tuple(module_results),
        l_index=l_result,
        business=business,
        powers=powers_result,
        triad=triad,
        composite=composite,
        gate_bands={m.key: m.gate_band for m in module_results},
        v_display_0_100=_round(v_stored * 100),
    )


# --- Modules & L ------------------------------------------------------------------------


def _score_modules(
    registry: Registry,
    coefficients: CoefficientSet,
    subs_by_key: dict[str, SubcomponentRating],
) -> tuple[list[ModuleResult], dict[str, float | None]]:
    module_results: list[ModuleResult] = []
    q_by_module: dict[str, float | None] = {}

    for module in registry.modules:
        alpha = coefficients.alpha_module[module.key]
        lambdas = coefficients.lambda_loadings[module.key]

        rows: list[SubcomponentRow] = []
        assessed: list[tuple[str, MaturityLevel]] = []  # (key, level), registry order
        critical_ratings: list[SubcomponentRating] = []
        n_applicable = n_assessed = n_na = 0

        for sub in module.subcomponents:
            rating = subs_by_key[sub.key]
            rows.append(
                SubcomponentRow(
                    key=sub.key,
                    critical=sub.critical,
                    level=rating.level.value if rating.level is not None else None,
                    index=rating.level.score_index if rating.level is not None else None,
                    evidence=rating.evidence_grade.value if rating.evidence_grade else None,
                    state=rating.state.value if rating.state is not None else None,
                )
            )
            if rating.state == NonScoreState.NOT_APPLICABLE:
                n_na += 1
            else:
                n_applicable += 1
                if rating.level is not None:
                    n_assessed += 1
                    assessed.append((sub.key, rating.level))
            if sub.critical:
                critical_ratings.append(rating)

        if assessed:
            num = sum(lambdas[key] * level.score_index for key, level in assessed)
            den = sum(lambdas[key] for key, _ in assessed)
            weighted_avg = num / den
            min_term = min(level.score_index for _, level in assessed)
            bottleneck = min(assessed, key=lambda kl: kl[1].score_index)[0]
            q_m: float | None = alpha * weighted_avg + (1 - alpha) * min_term
        else:
            weighted_avg = min_term = q_m = None
            bottleneck = None

        all_assessed_ranks = [level.rank for _, level in assessed]
        band, blocked, note = _rating_gate(critical_ratings, all_assessed_ranks)
        coverage = n_assessed / n_applicable if n_applicable else None

        q_by_module[module.key] = q_m
        module_results.append(
            ModuleResult(
                key=module.key,
                name=module.name,
                subcomponents=tuple(rows),
                n_applicable=n_applicable,
                n_assessed=n_assessed,
                n_not_applicable=n_na,
                coverage=_round(coverage) if coverage is not None else None,
                alpha=alpha,
                weighted_avg=_round(weighted_avg) if weighted_avg is not None else None,
                min_term=_round(min_term) if min_term is not None else None,
                bottleneck_subcomponent=bottleneck,
                q_m=_round(q_m) if q_m is not None else None,
                gate_band=band,
                gate_blocked=blocked,
                gate_note=note,
            )
        )
    return module_results, q_by_module


def _evidence_rank(evidence: EvidenceGrade | None) -> int:
    """An assessed subcomponent reaching the gate MUST carry an evidence grade (no `E1` default)."""
    if evidence is None:
        raise ValueError("Assessed subcomponent reached the gate without an evidence grade.")
    return evidence.rank


def _rating_gate(
    critical_ratings: list[SubcomponentRating], all_assessed_ranks: list[int]
) -> tuple[str, bool, str]:
    """Rule-based rating gate (Methodology v1.1 §5.2a): band = min(critical CEILING, bottleneck
    FLOOR). Never arithmetic on q_m. 'Basic' is reachable; a critical Not Assessed blocks."""
    assessed_crit = [r for r in critical_ratings if r.level is not None]
    blocked = any(r.state == NonScoreState.NOT_ASSESSED for r in critical_ratings)
    crit_ranks = [r.level.rank for r in assessed_crit if r.level is not None]

    if not assessed_crit and not blocked:
        ceiling_rank, ceiling_note = 4, "no critical subcomponent in scope"
    elif blocked:
        ceiling_rank, ceiling_note = 2, "gate blocked: a critical subcomponent is Not Assessed"
    elif all(
        r.level is not None and r.level.rank >= 3 and _evidence_rank(r.evidence_grade) >= 3
        for r in assessed_crit
    ):
        ceiling_rank, ceiling_note = 4, "all critical Advanced+ at E3+"
    elif min(crit_ranks) >= 2:
        ceiling_rank, ceiling_note = 3, "no critical is Basic"
    elif max(crit_ranks) == 1:
        ceiling_rank, ceiling_note = 1, "every critical is Basic"
    else:
        ceiling_rank, ceiling_note = 2, "a critical subcomponent is Basic"

    floor_rank = min(all_assessed_ranks) if all_assessed_ranks else 1
    if floor_rank >= 3:
        floor_cap = 4
    elif floor_rank == 2:
        floor_cap = 3
    elif all(r == 1 for r in all_assessed_ranks):
        floor_cap = 1  # every assessed subcomponent is Basic → the module is Basic (reachable)
    else:
        floor_cap = 2

    band_rank = min(ceiling_rank, floor_cap)
    if band_rank == ceiling_rank and ceiling_rank <= floor_cap:
        note = ceiling_note
    else:
        note = f"{ceiling_note}; capped by bottleneck ({_RANK_BAND[floor_rank]})"
    return (_RANK_BAND[band_rank], blocked, note)


def _score_l(
    registry: Registry,
    coefficients: CoefficientSet,
    q_by_module: dict[str, float | None],
) -> tuple[LResult, float]:
    """L = α_L·(Σδ·q_m / Σδ) + (1−α_L)·min(q over critical-for-L modules). A fully-unassessed
    module (q_m None) is EXCLUDED from both terms — never zero-filled (D9); δ renormalises."""
    assessed_q = {k: v for k, v in q_by_module.items() if v is not None}
    if not assessed_q:
        raise ValueError("Cannot compute L: no module has any assessed subcomponent.")
    num = sum(coefficients.delta[k] * v for k, v in assessed_q.items())
    den = sum(coefficients.delta[k] for k in assessed_q)
    l_weighted = num / den

    crit_q = [v for k in coefficients.critical_modules_for_l if (v := q_by_module[k]) is not None]
    if not crit_q:
        raise ValueError("Cannot compute L min term: no critical-for-L module is assessed.")
    l_min = min(crit_q)
    l_value = coefficients.alpha_l * l_weighted + (1 - coefficients.alpha_l) * l_min
    return (
        LResult(weighted_term=_round(l_weighted), min_term=_round(l_min), value=_round(l_value)),
        l_value,
    )


# --- Business (B) -----------------------------------------------------------------------


def _interpolate(metric: MetricDef, raw: float) -> float:
    """Piecewise-linear normalisation n_k(raw) → [0,1] against the metric's anchors (§5.3).
    Anchors are strictly ascending by raw (enforced on the registry); clamped outside the range."""
    anchors = metric.normalisation.anchors
    if not anchors:
        raise ValueError(f"Metric {metric.key} has no normalisation anchors.")
    pts = [(a.raw, a.normalised) for a in anchors]  # already strictly ascending by raw
    if raw <= pts[0][0]:
        return pts[0][1]
    if raw >= pts[-1][0]:
        return pts[-1][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:], strict=False):
        if x0 <= raw <= x1:
            t = (raw - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    raise AssertionError("unreachable")  # pragma: no cover


def _score_business(
    registry: Registry,
    coefficients: CoefficientSet,
    metrics_by_key: dict[str, MetricObservation],
) -> tuple[BusinessResult, dict[str, float], float]:
    """B = group-weighted mean (ADR-0006): within-group w_metric-weighted mean per group, then a
    W_g-weighted mean across groups. State metrics (N/A / Not Assessed) drop and their group
    renormalises. Returns the UNROUNDED group means too (the triad's Economic Value reads them)."""
    rows: list[MetricRow] = []
    group_terms: dict[str, tuple[float, float]] = {}  # group → (Σ w·n_k, Σ w)

    for metric in registry.metrics:
        obs = metrics_by_key[metric.key]
        state = obs.state
        n_k = None if state is not None else _interpolate(metric, _require_raw(obs))
        rows.append(
            MetricRow(
                key=metric.key,
                raw=None if state is not None else obs.raw,
                unit=metric.unit,
                direction=metric.direction,
                group=metric.group,
                state=state.value if state is not None else None,
                n_k=_round(n_k) if n_k is not None else None,
            )
        )
        if n_k is not None:
            if metric.group is None:
                raise ValueError(
                    f"Metric {metric.key!r} is scored into B but has no group; the group-weighted "
                    f"B is undefined for an ungrouped metric (ADR-0006)."
                )
            w = coefficients.w_metric[metric.key]
            acc_num, acc_den = group_terms.get(metric.group, (0.0, 0.0))
            group_terms[metric.group] = (acc_num + w * n_k, acc_den + w)

    group_means = {g: num / den for g, (num, den) in group_terms.items()}
    b_num = sum(coefficients.group_weights[g] * mean for g, mean in group_means.items())
    b_den = sum(coefficients.group_weights[g] for g in group_means)
    b_value = b_num / b_den
    business = BusinessResult(
        metrics=tuple(rows),
        group_means={g: _round(m) for g, m in group_means.items()},
        b_index=_round(b_value),
    )
    return business, group_means, b_value


def _require_raw(obs: MetricObservation) -> float:
    if obs.raw is None:  # pragma: no cover — guarded by the state branch above
        raise ValueError(f"Metric {obs.metric_key!r} has no raw value to normalise.")
    return obs.raw


# --- Powers (P) & triad -----------------------------------------------------------------


def _score_powers(
    registry: Registry,
    coefficients: CoefficientSet,
    powers_by_key: dict[str, PowerObservation],
) -> tuple[PowersResult, float]:
    """P = Σ w_j·strength_j / Σ w_j over ALL 7 powers, strength_j = the WEAKER of Benefit/Barrier
    (Helmer, §8). Powers are never N/A — every power is in the denominator."""
    enc = coefficients.strength_encoding
    rows: list[PowerRow] = []
    p_num = p_den = 0.0
    for power in registry.powers:
        obs = powers_by_key[power.key]
        benefit, barrier = obs.benefit.value, obs.barrier.value
        strength = benefit if enc[benefit] <= enc[barrier] else barrier
        value = enc[strength]
        w = coefficients.w_power[power.key]
        p_num += w * value
        p_den += w
        rows.append(
            PowerRow(
                key=power.key,
                benefit=benefit,
                barrier=barrier,
                strength=strength,
                value=_round(value),
            )
        )
    return PowersResult(powers=tuple(rows), p_index=_round(p_num / p_den)), p_num / p_den


def _derive_triad_thresholds(strength_encoding: dict[str, float]) -> list[tuple[str, float]]:
    """Nearest-named-level discretisation (ADR-0007): the band thresholds are the MIDPOINTS between
    adjacent strength-encoding anchors. Returned descending by threshold for `_to_ordinal`."""
    items = sorted(strength_encoding.items(), key=lambda kv: kv[1])  # ascending by encoded value
    thresholds: list[tuple[str, float]] = []
    for i in range(len(items) - 1, -1, -1):
        label, value = items[i]
        thr = 0.0 if i == 0 else (items[i - 1][1] + value) / 2
        thresholds.append((label, thr))
    return thresholds


def _to_ordinal(value: float, thresholds: list[tuple[str, float]]) -> str:
    for label, threshold in thresholds:
        if value >= threshold:
            return label
    raise AssertionError("unreachable — thresholds include 0.0")  # pragma: no cover


def _score_triad(
    registry: Registry,
    coefficients: CoefficientSet,
    powers_by_key: dict[str, PowerObservation],
    group_means: dict[str, float],
) -> TriadResult:
    """Derive the Platform Power triad (§2) from the split power data + B's group signal. Ordinal
    out (ADR-0002): each dimension reports a rating; the score is audit-only."""
    enc = coefficients.strength_encoding
    thresholds = _derive_triad_thresholds(enc)

    barriers = [enc[powers_by_key[p.key].barrier.value] for p in registry.powers]
    defence = sum(barriers) / len(barriers)

    perceived_src = [powers_by_key[k] for k in _PERCEIVED_POWERS if k in powers_by_key]
    perceived = (
        sum(enc[o.benefit.value] for o in perceived_src) / len(perceived_src)
        if perceived_src
        else None
    )

    econ_src = [group_means[g] for g in _ECONOMIC_GROUPS if g in group_means]
    # No assessed scale/unit-economics metric ⟹ Economic Value is Not Assessed (None), never a
    # "None" moat floor. Zero-filling would conflate unassessed with "no economic value" (D9).
    economic = sum(econ_src) / len(econ_src) if econ_src else None

    def _dim(v: float | None) -> TriadDimensionResult:
        if v is None:
            return TriadDimensionResult(rating=None, score=None)
        return TriadDimensionResult(rating=_to_ordinal(v, thresholds), score=_round(v))

    return TriadResult(
        economic_value=_dim(economic),
        perceived_value=_dim(perceived),
        defence_value=_dim(defence),
    )


# --- Fail-loud input coverage -----------------------------------------------------------


def _assert_inputs_cover_registry(inputs: AssessmentInputs, registry: Registry) -> None:
    """Inputs must cover the registry EXACTLY — the same discipline ADR-0001 enforces for
    coefficients. A missing or extra key aborts the score (never a default, never a partial run)."""
    _assert_exact(
        "subcomponent",
        registry.all_subcomponent_keys(),
        {r.subcomponent_key for r in inputs.subcomponents},
    )
    _assert_exact("metric", registry.metric_keys(), {m.metric_key for m in inputs.metrics})
    _assert_exact("power", registry.power_keys(), {p.power_key for p in inputs.powers})


def _assert_exact(dimension: str, legal: frozenset[str], supplied: set[str]) -> None:
    missing = legal - supplied
    extra = supplied - legal
    if missing or extra:
        raise ValueError(
            f"{dimension} inputs must cover the registry exactly. "
            f"Missing: {sorted(missing)}; extra: {sorted(extra)}."
        )
