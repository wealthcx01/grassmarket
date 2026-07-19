"""Registry tests (ADR-0001) — an unknown or missing key is a refusal, never a default.

These are the tests that would have turned prototype defects D1, D4, D7 from silent wrong
numbers into load-time crashes.
"""

from __future__ import annotations

import pytest
from bcap_contracts.common import PowerLifecycleStage
from bcap_contracts.registry import (
    AnchorPoint,
    EmptyDimensionError,
    MetricDef,
    MissingKeyError,
    ModuleDef,
    NormalisationSpec,
    PowerDef,
    Registry,
    RegistryError,
    SubcomponentDef,
    UnknownKeyError,
    _build_registry,
    _parse_metric,
    load_registry,
)
from pydantic import ValidationError


def test_settled_powers_are_the_seven() -> None:
    r = load_registry()
    assert r.power_keys() == {
        "SCALE_ECONOMIES",
        "NETWORK_ECONOMIES",
        "COUNTER_POSITIONING",
        "SWITCHING_COSTS",
        "BRANDING",
        "CORNERED_RESOURCE",
        "PROCESS_POWER",
    }


def test_nine_modules_with_fifty_one_subcomponents() -> None:
    r = load_registry()
    assert len(r.module_keys()) == 9
    # GRS-0002 populated the 51-subcomponent draft (6+7+7+5+6+6+6+4+4).
    assert len(r.all_subcomponent_keys()) == 51
    assert r.subcomponent_status == "draft-pending-ratification"
    # Every module has at least one critical subcomponent (needed by the rating gate, §5.2).
    for m in r.modules:
        assert any(s.critical for s in m.subcomponents), f"{m.key} has no critical subcomponent"
    # Descriptions are carried through for wizard guidance.
    assert r.require_subcomponent("FRONTEND", "FRONTEND_PERFORMANCE").description
    # Every subcomponent key is fully qualified to <MODULE_KEY>_<LEAF> (GRS-0002a).
    for m in r.modules:
        for s in m.subcomponents:
            assert s.key.startswith(m.key + "_"), f"{s.key} not qualified under {m.key}"
    # Keys are globally unique, not merely per-module.
    assert len(r.all_subcomponent_keys()) == sum(len(m.subcomponents) for m in r.modules)


def test_metric_register_is_populated_draft() -> None:
    r = load_registry()
    assert len(r.metric_keys()) == 10
    assert r.metric_status == "draft-pending-ratification"
    metric = r.require_metric("COST_TO_SERVE")
    assert metric.unit == "GBP_per_year"
    assert metric.direction == "lower_is_better"
    # Anchors are ordered by ascending raw; lower_is_better → normalised descends.
    raws = [a.raw for a in metric.normalisation.anchors]
    norms = [a.normalised for a in metric.normalisation.anchors]
    assert raws == sorted(raws)
    assert norms == sorted(norms, reverse=True)


def test_metric_domain_bounds_reject_impossible_values() -> None:
    # GRS-0144 / ADR-0035: a non-negative magnitude carries min_raw=0 and refuses a negative or
    # non-finite raw, but a valid (even extreme) positive value is fine — it clamps in the engine.
    r = load_registry()
    aua = r.require_metric("AUA")
    assert aua.min_raw == 0
    assert aua.domain_violation(-999_999) is not None
    assert aua.domain_violation(float("nan")) is not None
    assert aua.domain_violation(float("inf")) is not None
    assert aua.domain_violation(1_800_000_000) is None  # a real value scores
    assert aua.domain_violation(1) is None  # below lowest anchor but valid → clamps, not refused


def test_signed_metrics_allow_negative_values() -> None:
    # A margin or a growth rate can legitimately be negative (loss-making / shrinking) — those
    # metrics leave min_raw None so a negative is a valid input, not a refusal.
    r = load_registry()
    for key in ("GROSS_MARGIN", "CLIENT_GROWTH_RATE"):
        metric = r.require_metric(key)
        assert metric.min_raw is None
        assert metric.domain_violation(-5) is None
        assert metric.domain_violation(float("nan")) is not None  # non-finite still refused


def test_scoreability_refuses_an_out_of_domain_metric() -> None:
    # A negative AUA (impossible) surfaces as a fail-loud scoreability blocker naming the metric —
    # never clamped into the anchor curve, never a 500 (GRS-0144).
    from bcap_contracts.assessments import AssessmentDocument, MetricEntry

    from grassmarket.assessments.service import scoreability_blockers

    r = load_registry()
    doc = AssessmentDocument(metrics=(MetricEntry(metric_key="AUA", raw=-999_999),))
    blockers = scoreability_blockers(doc, r)
    assert any("Assets Under Administration" in b and "can't be below" in b for b in blockers)


def test_metricentry_rejects_non_finite_raw() -> None:
    from bcap_contracts.assessments import MetricEntry

    with pytest.raises(ValidationError):
        MetricEntry(metric_key="AUA", raw=float("nan"))
    with pytest.raises(ValidationError):
        MetricEntry(metric_key="AUA", raw=float("inf"))


def test_require_unknown_power_raises() -> None:
    r = load_registry()
    with pytest.raises(UnknownKeyError):
        r.require_power("NOT_A_POWER")


def test_require_unknown_module_raises() -> None:
    r = load_registry()
    with pytest.raises(UnknownKeyError):
        r.require_module("BACK_OFFICE")  # the exact D1 typo — must NOT resolve to BACKOFFICE


def test_assert_covers_exact_set() -> None:
    r = _tiny_registry()
    # Exactly the module set → OK.
    r.assert_covers_keys("module", r.module_keys(), {"M1"})


def test_assert_covers_unknown_key_raises() -> None:
    r = _tiny_registry()
    with pytest.raises(UnknownKeyError):
        r.assert_covers_keys("module", r.module_keys(), {"M1", "M_TYPO"})


def test_assert_covers_missing_key_raises() -> None:
    r = _tiny_registry(extra_module=True)
    with pytest.raises(MissingKeyError):
        r.assert_covers_keys("module", r.module_keys(), {"M1"})  # M2 missing


def test_assert_covers_empty_dimension_raises() -> None:
    # The real registry's dimensions are now populated, so build one with a genuinely empty
    # metric dimension to exercise the refusal (ADR-0001 scope note).
    r = Registry(metrics=())
    with pytest.raises(EmptyDimensionError):
        r.assert_covers_keys("metric", r.metric_keys(), set())


def test_duplicate_keys_rejected_at_construction() -> None:
    from bcap_contracts.registry import RegistryError, _assert_unique_keys

    dup = Registry(
        powers=(
            PowerDef(
                key="X", name="X", lifecycle_stage=PowerLifecycleStage.TAKEOFF, description="d"
            ),
            PowerDef(
                key="X", name="X2", lifecycle_stage=PowerLifecycleStage.TAKEOFF, description="d"
            ),
        )
    )
    with pytest.raises(RegistryError):
        _assert_unique_keys(dup)


# --- GRS-0002a: fail-loud status, closed sets, anchor invariants, global uniqueness ---------


def _metric_raw(**overrides: object) -> dict:
    base = {
        "key": "K",
        "name": "K",
        "description": "A test metric.",
        "unit": "count",
        "direction": "higher_is_better",
        "status": "settled",
        "normalisation": {
            "anchors": [{"raw": 0, "normalised": 0.2}, {"raw": 10, "normalised": 0.8}]
        },
    }
    base.update(overrides)
    return base


def test_status_less_module_set_refuses_to_load() -> None:
    # A dataset that omits `status:` on the module set must refuse — never default to "settled".
    with pytest.raises(RegistryError, match="status"):
        _build_registry({}, {"modules": []}, {"status": "settled", "metrics": []})


def test_status_less_metric_set_refuses_to_load() -> None:
    with pytest.raises(RegistryError, match="status"):
        _build_registry({}, {"status": "settled", "modules": []}, {"metrics": []})


def test_status_less_metric_def_refuses_to_load() -> None:
    # Each MetricDef requires its own status via bracket access (no `.get(..., "settled")`).
    raw = _metric_raw()
    del raw["status"]
    with pytest.raises(RegistryError, match="status"):
        _parse_metric(raw)


def test_unknown_direction_refuses_to_load() -> None:
    with pytest.raises(ValidationError):
        _parse_metric(_metric_raw(direction="higher"))  # typo — not in the closed set


def test_unknown_group_refuses_to_load() -> None:
    with pytest.raises(ValidationError):
        _parse_metric(_metric_raw(group="scaale"))  # typo — not scale/unit_economics/momentum


def test_unknown_normalisation_method_refuses_to_load() -> None:
    with pytest.raises(ValidationError):
        NormalisationSpec(method="loglinear")  # not piecewise_linear/percentile


def test_none_group_is_allowed() -> None:
    assert _parse_metric(_metric_raw()).group is None


def test_piecewise_linear_requires_anchors() -> None:
    with pytest.raises(RegistryError, match="anchor"):
        NormalisationSpec(method="piecewise_linear", anchors=())


def test_anchors_must_ascend_by_raw() -> None:
    with pytest.raises(RegistryError, match="ascending"):
        NormalisationSpec(
            anchors=(AnchorPoint(raw=10, normalised=0.2), AnchorPoint(raw=5, normalised=0.5))
        )


def test_anchor_raws_must_be_strictly_ascending() -> None:
    # Equal raws are not strictly ascending — a flat breakpoint can't be interpolated.
    with pytest.raises(RegistryError, match="ascending"):
        NormalisationSpec(
            anchors=(AnchorPoint(raw=5, normalised=0.2), AnchorPoint(raw=5, normalised=0.5))
        )


def test_anchor_normalised_must_be_monotonic() -> None:
    with pytest.raises(RegistryError, match="monotonic"):
        NormalisationSpec(
            anchors=(
                AnchorPoint(raw=1, normalised=0.2),
                AnchorPoint(raw=2, normalised=0.8),
                AnchorPoint(raw=3, normalised=0.5),  # zig-zag
            )
        )


def test_higher_is_better_with_descending_curve_refuses() -> None:
    with pytest.raises(RegistryError, match="descends"):
        _parse_metric(
            _metric_raw(
                direction="higher_is_better",
                normalisation={
                    "anchors": [{"raw": 1, "normalised": 0.8}, {"raw": 2, "normalised": 0.2}]
                },
            )
        )


def test_lower_is_better_with_ascending_curve_refuses() -> None:
    with pytest.raises(RegistryError, match="ascends"):
        _parse_metric(
            _metric_raw(
                direction="lower_is_better",
                normalisation={
                    "anchors": [{"raw": 1, "normalised": 0.2}, {"raw": 2, "normalised": 0.8}]
                },
            )
        )


def test_global_subcomponent_key_collision_refuses() -> None:
    # Two modules sharing a subcomponent key is a load-time refusal (global uniqueness, GRS-0002a).
    from bcap_contracts.registry import _assert_unique_keys

    dup = Registry(
        modules=(
            ModuleDef(
                key="M1",
                name="M1",
                description="d",
                subcomponents=(SubcomponentDef(key="SHARED", name="s", module_key="M1"),),
            ),
            ModuleDef(
                key="M2",
                name="M2",
                description="d",
                subcomponents=(SubcomponentDef(key="SHARED", name="s", module_key="M2"),),
            ),
        )
    )
    with pytest.raises(RegistryError, match="globally unique"):
        _assert_unique_keys(dup)


def _tiny_registry(extra_module: bool = False) -> Registry:
    modules = [
        ModuleDef(
            key="M1",
            name="Module 1",
            description="d",
            subcomponents=(
                SubcomponentDef(key="M1_A", name="A", module_key="M1", critical=True),
                SubcomponentDef(key="M1_B", name="B", module_key="M1"),
            ),
        )
    ]
    if extra_module:
        modules.append(ModuleDef(key="M2", name="Module 2", description="d"))
    return Registry(
        powers=(
            PowerDef(
                key="P1",
                name="Power 1",
                lifecycle_stage=PowerLifecycleStage.TAKEOFF,
                description="d",
            ),
        ),
        modules=tuple(modules),
        metrics=(
            MetricDef(
                key="K1",
                name="Metric 1",
                description="A test metric.",
                unit="count",
                direction="higher_is_better",
                normalisation=NormalisationSpec(
                    anchors=(
                        AnchorPoint(raw=0, normalised=0.2),
                        AnchorPoint(raw=1, normalised=0.8),
                    )
                ),
            ),
        ),
    )
