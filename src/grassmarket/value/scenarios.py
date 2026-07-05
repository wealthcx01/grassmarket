"""Scenario prioritisation — SCORE domain only (Methodology §10, ADR-0002).

A scenario is evaluated by FULL RE-SCORING: run `score()` on the baseline and on the scenario
inputs and diff V. Prioritisation is the ΔV ranking — the Upgrade Priority Index. There is no LV
formula, no κ, and nothing in this module touches currency (that separation is the point). The
prototype's `LV = κ·Δq/(1+r) − cost` — pounds subtracted from score-points — is defect D2, and it
is simply not expressible here.
"""

from __future__ import annotations

from bcap_contracts.assessments import CoefficientSet
from bcap_contracts.registry import Registry
from bcap_contracts.value import ScenarioResult, UpgradePriority

from grassmarket.atlas import AssessmentInputs, score


def evaluate_scenario(
    name: str,
    baseline: AssessmentInputs,
    scenario: AssessmentInputs,
    coefficients: CoefficientSet,
    registry: Registry,
) -> ScenarioResult:
    """Evaluate one scenario by full re-scoring: ΔV (and ΔL/ΔB/ΔP) between baseline and scenario.
    Wholly score-domain — the same kernel, twice, differenced."""
    base = score(baseline, coefficients, registry).composite
    scen = score(scenario, coefficients, registry).composite
    return ScenarioResult(
        name=name,
        baseline_v=base.v_index,
        scenario_v=scen.v_index,
        delta_v=round(scen.v_index - base.v_index, 6),
        delta_l=round(scen.l_index - base.l_index, 6),
        delta_b=round(scen.b_index - base.b_index, 6),
        delta_p=round(scen.p_index - base.p_index, 6),
    )


def prioritise_upgrades(
    baseline: AssessmentInputs,
    scenarios: list[tuple[str, AssessmentInputs]],
    coefficients: CoefficientSet,
    registry: Registry,
) -> list[UpgradePriority]:
    """The Upgrade Priority Index: evaluate each candidate scenario against the baseline and rank by
    ΔV descending. Ties keep input order (stable sort). The index RANKS; it never prices."""
    results = [
        evaluate_scenario(name, baseline, scenario, coefficients, registry)
        for name, scenario in scenarios
    ]
    ordered = sorted(results, key=lambda r: r.delta_v, reverse=True)
    return [
        UpgradePriority(name=r.name, delta_v=r.delta_v, rank=rank)
        for rank, r in enumerate(ordered, start=1)
    ]
