"""The value layer — GRS-0006, Methodology v1.1 §10.

Two domains, held strictly apart (ADR-0002): `scenarios` prioritises in the SCORE domain (ΔV from
full re-scoring → the Upgrade Priority Index); `bridge` prices in the CURRENCY domain (cost + lever
NPVs as `Money`) and rates strategy in the ORDINAL domain. No function anywhere in this package
takes both a Score and a Money — the AST scan (`test_money_and_adr0002`) enforces it.
"""

from __future__ import annotations

from grassmarket.value.bridge import (
    cost_estimate,
    cost_to_serve_lever,
    incident_expected_loss_lever,
    project_drag_lever,
    render_assumption_register,
    revenue_enablement_lever,
    strategic_rating,
)
from grassmarket.value.scenarios import evaluate_scenario, prioritise_upgrades

__all__ = [
    "evaluate_scenario",
    "prioritise_upgrades",
    "cost_estimate",
    "cost_to_serve_lever",
    "project_drag_lever",
    "incident_expected_loss_lever",
    "revenue_enablement_lever",
    "strategic_rating",
    "render_assumption_register",
]
