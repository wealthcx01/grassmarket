"""Property tests for the ATLAS engine (GRS-0004, CLAUDE.md testing rules).

Deterministic and enumerated (no RNG): each test constructs explicit inputs over the real registry
and asserts a structural guarantee of Methodology v1.1 §5. These must FAIL if the feature is wrong —
they check behaviour (V never drops, the bottleneck dominates, N/A renormalises, Not Assessed is
excluded, powers are never dropped, the gate obeys §5.2a), not just that a number came out.
"""

from __future__ import annotations

import pytest
from bcap_contracts.assessments import SubcomponentRating
from bcap_contracts.common import EvidenceGrade, MaturityLevel, NonScoreState, StrengthRating
from bcap_contracts.registry import Registry, load_registry

from grassmarket.atlas import AssessmentInputs, MetricObservation, PowerObservation, score
from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set

_L = MaturityLevel
_E3 = EvidenceGrade.E3_ARTIFACT

# A sub override is a level (assessed at E3), a (level, evidence) pair, or a non-score state.
SubValue = MaturityLevel | tuple[MaturityLevel, EvidenceGrade] | NonScoreState


@pytest.fixture(scope="module")
def registry() -> Registry:
    return load_registry()


@pytest.fixture(scope="module")
def coeffs(registry: Registry):
    return draft_v1_coefficient_set(registry)


def _default_metric_raw(registry: Registry, key: str) -> float:
    """A valid mid-range raw for a metric — the second anchor's raw (inside the anchor range)."""
    anchors = registry.require_metric(key).normalisation.anchors
    return anchors[1].raw


def build_inputs(
    registry: Registry,
    *,
    subs: dict[str, SubValue] | None = None,
    metrics: dict[str, float | NonScoreState] | None = None,
    powers: dict[str, tuple[StrengthRating, StrengthRating]] | None = None,
    default_level: MaturityLevel = _L.DEVELOPING,
) -> AssessmentInputs:
    """A complete, registry-covering assessment: every subcomponent at ``default_level`` (E3),
    every metric at its mid anchor, every power (Emerging, Emerging) — with overrides applied."""
    subs = subs or {}
    metrics = metrics or {}
    powers = powers or {}

    sub_ratings: list[SubcomponentRating] = []
    for module in registry.modules:
        for sub in module.subcomponents:
            value: SubValue = subs.get(sub.key, default_level)
            if isinstance(value, NonScoreState):
                sub_ratings.append(
                    SubcomponentRating(module_key=module.key, subcomponent_key=sub.key, state=value)
                )
            elif isinstance(value, tuple):
                level, evidence = value
                sub_ratings.append(
                    SubcomponentRating(
                        module_key=module.key,
                        subcomponent_key=sub.key,
                        level=level,
                        evidence_grade=evidence,
                    )
                )
            else:
                sub_ratings.append(
                    SubcomponentRating(
                        module_key=module.key,
                        subcomponent_key=sub.key,
                        level=value,
                        evidence_grade=_E3,
                    )
                )

    metric_obs: list[MetricObservation] = []
    for m in registry.metrics:
        override = metrics.get(m.key)
        if isinstance(override, NonScoreState):
            metric_obs.append(MetricObservation(metric_key=m.key, state=override))
        else:
            raw = override if override is not None else _default_metric_raw(registry, m.key)
            metric_obs.append(MetricObservation(metric_key=m.key, raw=float(raw)))

    power_obs = [
        PowerObservation(
            power_key=p.key,
            benefit=powers.get(p.key, (StrengthRating.EMERGING, StrengthRating.EMERGING))[0],
            barrier=powers.get(p.key, (StrengthRating.EMERGING, StrengthRating.EMERGING))[1],
        )
        for p in registry.powers
    ]
    return AssessmentInputs(
        subcomponents=tuple(sub_ratings), metrics=tuple(metric_obs), powers=tuple(power_obs)
    )


def _v(registry: Registry, coeffs, **kw) -> float:
    return score(build_inputs(registry, **kw), coeffs, registry).composite.v_index


# --- Monotonicity: raising any subcomponent never lowers V ------------------------------


def test_monotonicity_raising_any_subcomponent_never_lowers_v(registry: Registry, coeffs) -> None:
    all_keys = sorted(registry.all_subcomponent_keys())
    # From an all-Developing floor, raise each single subcomponent to Advanced.
    base_dev = _v(registry, coeffs, default_level=_L.DEVELOPING)
    for key in all_keys:
        raised = _v(registry, coeffs, default_level=_L.DEVELOPING, subs={key: _L.ADVANCED})
        assert raised >= base_dev - 1e-12, f"raising {key} Developing→Advanced lowered V"
    # And from an all-Advanced floor, raise each to Frontier (covers the top step too).
    base_adv = _v(registry, coeffs, default_level=_L.ADVANCED)
    for key in all_keys:
        raised = _v(registry, coeffs, default_level=_L.ADVANCED, subs={key: _L.FRONTIER})
        assert raised >= base_adv - 1e-12, f"raising {key} Advanced→Frontier lowered V"


def test_monotonicity_is_strict_somewhere(registry: Registry, coeffs) -> None:
    # Sanity: the relation isn't vacuously satisfied by V never moving.
    base = _v(registry, coeffs, default_level=_L.DEVELOPING)
    all_up = _v(registry, coeffs, default_level=_L.ADVANCED)
    assert all_up > base


# --- Bottleneck: raising the min helps q_m at least as much as raising the max -----------


def test_bottleneck_raising_min_dominates_raising_max(registry: Registry, coeffs) -> None:
    """q_m = α·avg + (1−α)·min. Raising the (unique) minimum by an index step Δ gains an extra
    (1−α)·Δ over raising the maximum by the same Δ. Use FRONTEND: one Basic (unique min) + five
    Developing (max); both Basic→Developing and Developing→Advanced are the same Δ = 0.3 step."""
    module = "FRONTEND"
    keys = [s.key for s in registry.require_module(module).subcomponents]
    min_key, max_key = keys[0], keys[1]

    base_subs = {min_key: _L.BASIC} | {k: _L.DEVELOPING for k in keys[1:]}

    def qm(subs: dict[str, SubValue]) -> float:
        res = score(build_inputs(registry, subs=subs), coeffs, registry)
        qm_val = next(m.q_m for m in res.modules if m.key == module)
        assert qm_val is not None
        return qm_val

    base = qm(base_subs)
    raise_min = qm({**base_subs, min_key: _L.DEVELOPING})  # Basic→Developing (Δ 0.3), unique min
    raise_max = qm({**base_subs, max_key: _L.ADVANCED})  # Developing→Advanced (Δ 0.3)
    delta_min = raise_min - base
    delta_max = raise_max - base
    assert delta_min >= delta_max - 1e-9
    # α = 0.7, Δ = 0.3 → the extra should be (1−α)·Δ = 0.09.
    assert delta_min - delta_max == pytest.approx(0.09, abs=1e-6)


# --- N/A renormalisation (subcomponents AND metrics) ------------------------------------


def test_na_subcomponent_renormalises_not_zero_fills(registry: Registry, coeffs) -> None:
    module = "FRONTEND"
    keys = [s.key for s in registry.require_module(module).subcomponents]
    non_critical = next(
        s.key for s in registry.require_module(module).subcomponents if not s.critical
    )
    all_advanced = {k: _L.ADVANCED for k in keys}
    with_na = {**all_advanced, non_critical: NonScoreState.NOT_APPLICABLE}

    res = score(build_inputs(registry, subs=with_na), coeffs, registry)
    m = next(x for x in res.modules if x.key == module)
    # Renormalised: the N/A subcomponent is dropped, so q_m is still 0.8 (all remaining Advanced),
    # NOT dragged down by a zero-filled slot (D9). Coverage and counts exclude it.
    assert m.q_m == 0.8
    assert m.n_not_applicable == 1
    assert m.n_applicable == len(keys) - 1
    assert m.coverage == 1.0  # every APPLICABLE subcomponent is assessed


def test_na_metric_renormalises_its_group(registry: Registry, coeffs) -> None:
    # AUA is a `scale` metric; mark it N/A and the scale-group mean must be the mean of the OTHER
    # scale metrics only — the group renormalises, AUA is not zero-filled.
    res = score(
        build_inputs(registry, metrics={"AUA": NonScoreState.NOT_APPLICABLE}), coeffs, registry
    )
    aua_row = next(r for r in res.business.metrics if r.key == "AUA")
    assert aua_row.n_k is None and aua_row.state == NonScoreState.NOT_APPLICABLE.value
    scale_nks = [
        r.n_k
        for r in res.business.metrics
        if r.group == "scale" and r.n_k is not None and r.key != "AUA"
    ]
    expected = round(sum(scale_nks) / len(scale_nks), 6)
    assert res.business.group_means["scale"] == expected


# --- Not Assessed is excluded and taints coverage/gate ----------------------------------


def test_not_assessed_subcomponent_excluded_and_taints_coverage(registry: Registry, coeffs) -> None:
    module = "FRONTEND"
    keys = [s.key for s in registry.require_module(module).subcomponents]
    non_critical = next(
        s.key for s in registry.require_module(module).subcomponents if not s.critical
    )
    subs = {k: _L.ADVANCED for k in keys} | {non_critical: NonScoreState.NOT_ASSESSED}
    res = score(build_inputs(registry, subs=subs), coeffs, registry)
    m = next(x for x in res.modules if x.key == module)
    # Not Assessed stays IN the applicable count but contributes to no score; coverage < 1.
    assert m.n_applicable == len(keys)
    assert m.n_assessed == len(keys) - 1
    assert m.coverage == round((len(keys) - 1) / len(keys), 6)
    assert m.q_m == 0.8  # the remaining assessed are all Advanced; the NA slot is not zero-filled


def test_critical_not_assessed_blocks_the_gate(registry: Registry, coeffs) -> None:
    module = "FRONTEND"
    critical = next(s.key for s in registry.require_module(module).subcomponents if s.critical)
    subs = {critical: NonScoreState.NOT_ASSESSED}  # rest default Developing
    res = score(build_inputs(registry, subs=subs), coeffs, registry)
    m = next(x for x in res.modules if x.key == module)
    assert m.gate_blocked is True
    assert m.gate_band in {"Basic", "Developing"}  # ceiling is Developing when a critical is NA


# --- Powers are never N/A: all 7 always in the P denominator ----------------------------


def test_powers_never_na_denominator_is_always_seven(registry: Registry, coeffs) -> None:
    res = score(build_inputs(registry), coeffs, registry)
    assert len(res.powers.powers) == 7
    values = [p.value for p in res.powers.powers]
    assert res.powers.p_index == round(sum(values) / 7, 6)
    # Even an all-None power stays in scope (weakens P, never dropped).
    none_pair = (StrengthRating.NONE, StrengthRating.NONE)
    res2 = score(build_inputs(registry, powers={"SCALE_ECONOMIES": none_pair}), coeffs, registry)
    assert len(res2.powers.powers) == 7
    assert res2.powers.p_index < res.powers.p_index  # None drags P down, not out


def test_power_strength_is_the_weaker_side(registry: Registry, coeffs) -> None:
    # Established benefit but None barrier → the power is only as strong as its weaker (None) side.
    one_sided = {"SCALE_ECONOMIES": (StrengthRating.ESTABLISHED, StrengthRating.NONE)}
    res = score(build_inputs(registry, powers=one_sided), coeffs, registry)
    scale = next(p for p in res.powers.powers if p.key == "SCALE_ECONOMIES")
    assert scale.strength == "None"
    assert scale.value == 0.0


# --- Gate consistency vs §5.2a ----------------------------------------------------------


def test_gate_all_basic_module_is_basic(registry: Registry, coeffs) -> None:
    # "Basic" is a reachable band (not floored at Developing).
    for module in registry.modules:
        keys = [s.key for s in module.subcomponents]
        subs = {k: _L.BASIC for k in keys}
        res = score(build_inputs(registry, subs=subs), coeffs, registry)
        m = next(x for x in res.modules if x.key == module.key)
        assert m.gate_band == "Basic", f"{module.key} all-Basic should be Basic, got {m.gate_band}"


def test_gate_never_frontier_with_any_basic_part(registry: Registry, coeffs) -> None:
    # Criticals strong (Advanced/E3+), one non-critical Basic → the bottleneck floor bars Frontier.
    for module in registry.modules:
        subs: dict[str, SubValue] = {}
        non_critical_seen = False
        for s in module.subcomponents:
            if s.critical:
                subs[s.key] = (_L.ADVANCED, EvidenceGrade.E3_ARTIFACT)
            elif not non_critical_seen:
                subs[s.key] = _L.BASIC
                non_critical_seen = True
            else:
                subs[s.key] = (_L.ADVANCED, EvidenceGrade.E3_ARTIFACT)
        if not non_critical_seen:
            continue  # module with only critical subcomponents — skip
        res = score(build_inputs(registry, subs=subs), coeffs, registry)
        m = next(x for x in res.modules if x.key == module.key)
        assert m.gate_band != "Frontier", f"{module.key} is Frontier despite a Basic part"


def test_gate_frontier_reachable_when_all_advanced_e3(registry: Registry, coeffs) -> None:
    # All subcomponents Advanced at E3 (criticals included) → the module can reach Frontier.
    module = registry.modules[0]
    keys = [s.key for s in module.subcomponents]
    subs = {k: (_L.ADVANCED, EvidenceGrade.E3_ARTIFACT) for k in keys}
    res = score(build_inputs(registry, subs=subs), coeffs, registry)
    m = next(x for x in res.modules if x.key == module.key)
    assert m.gate_band == "Frontier"
