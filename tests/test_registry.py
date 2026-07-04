"""Registry tests (ADR-0001) — an unknown or missing key is a refusal, never a default.

These are the tests that would have turned prototype defects D1, D4, D7 from silent wrong
numbers into load-time crashes.
"""

from __future__ import annotations

import pytest
from bcap_contracts.common import PowerLifecycleStage
from bcap_contracts.registry import (
    EmptyDimensionError,
    MetricDef,
    MissingKeyError,
    ModuleDef,
    PowerDef,
    Registry,
    SubcomponentDef,
    UnknownKeyError,
    load_registry,
)


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
    assert r.require_subcomponent("FRONTEND", "PERFORMANCE").description


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
        metrics=(MetricDef(key="K1", name="Metric 1", unit="count", direction="higher_is_better"),),
    )
