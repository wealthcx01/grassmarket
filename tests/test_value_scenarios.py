"""Scenario prioritisation tests (GRS-0006, §10) — score domain only, no currency in sight."""

from __future__ import annotations

import pytest
from bcap_contracts.common import MaturityLevel
from bcap_contracts.registry import Registry, load_registry

from grassmarket.atlas.draft_coefficients import draft_v1_coefficient_set
from grassmarket.value import evaluate_scenario, prioritise_upgrades
from tests._atlas_inputs import meridian_inputs, override

_L = MaturityLevel


@pytest.fixture(scope="module")
def registry() -> Registry:
    return load_registry()


@pytest.fixture(scope="module")
def coeffs(registry: Registry):
    return draft_v1_coefficient_set(registry)


def test_upgrading_a_bottleneck_raises_v(registry, coeffs) -> None:
    baseline = meridian_inputs()
    # OEMS_EXEC_ALGOS is Basic and the bottleneck of OEMS (a critical-for-L module). Raising it
    # lifts L and therefore V — a positive ΔV in the pure score domain.
    scenario = override(baseline, "OEMS_EXEC_ALGOS", _L.ADVANCED)
    res = evaluate_scenario("Fix OEMS execution algos", baseline, scenario, coeffs, registry)
    assert res.delta_v > 0
    assert res.scenario_v > res.baseline_v
    # Only L moves — the upgrade is a subcomponent, so B and P are unchanged.
    assert res.delta_b == 0.0
    assert res.delta_p == 0.0
    assert res.delta_l > 0


def test_upgrade_priority_index_ranks_by_delta_v(registry, coeffs) -> None:
    baseline = meridian_inputs()
    # A bottleneck fix in a critical-for-L module vs a top-up of an already-Advanced sub.
    big = override(baseline, "OEMS_EXEC_ALGOS", _L.ADVANCED)  # Basic → Advanced in critical OEMS
    small = override(baseline, "APP_SERVER_OBSERVABILITY", _L.FRONTIER)  # Advanced → Frontier
    index = prioritise_upgrades(
        baseline,
        [("Top-up observability", small), ("Fix OEMS execution algos", big)],
        coeffs,
        registry,
    )
    assert [u.rank for u in index] == [1, 2]
    assert index[0].name == "Fix OEMS execution algos"  # bigger ΔV ranks first regardless of order
    assert index[0].delta_v >= index[1].delta_v
    assert all(u.delta_v > 0 for u in index)


def test_no_op_scenario_has_zero_delta(registry, coeffs) -> None:
    baseline = meridian_inputs()
    res = evaluate_scenario("No change", baseline, baseline, coeffs, registry)
    assert res.delta_v == 0.0
    assert res.baseline_v == res.scenario_v
