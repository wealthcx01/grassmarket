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


def test_nine_module_keys_present_with_empty_subcomponents() -> None:
    r = load_registry()
    assert len(r.module_keys()) == 9
    # Subcomponents are Loop 1 content — empty for now, by design.
    assert r.all_subcomponent_keys() == frozenset()


def test_metric_register_is_empty_in_loop0() -> None:
    assert load_registry().metric_keys() == frozenset()


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
    r = load_registry()
    with pytest.raises(EmptyDimensionError):
        r.assert_covers_keys("metric", r.metric_keys(), set())  # metric dimension is empty


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
        metrics=(MetricDef(key="K1", name="Metric 1", direction="higher_is_better"),),
    )
