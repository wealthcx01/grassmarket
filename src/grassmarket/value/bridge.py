"""The value bridge — CURRENCY and ORDINAL domains (Methodology §10, ADR-0002).

Three separated computations, none of which touches a `Score`:

- **Cost** (layer 1) — effort × rate → `Money`.
- **Levers** (layer 2) — each evidenced lever's risk-adjusted NPV → `Money`, every figure traceable
  to a client-supplied baseline in the assumption register.
- **Strategic** (layer 3) — moat/durability as an ORDINAL rating, never a decimal.

Money is combined only with Money (same currency). No function here names both a Score and a Money —
the ADR-0002 boundary, enforced structurally and by the AST scan.
"""

from __future__ import annotations

from collections.abc import Sequence

from bcap_contracts.common import StrengthRating
from bcap_contracts.money import Currency, Money
from bcap_contracts.value import (
    AssumptionRegister,
    CostEstimate,
    LeverKind,
    LeverValuation,
    StrategicRating,
)


def _pounds_to_money(pounds: float, currency: Currency, ref: str) -> Money:
    """Convert a pounds (major-unit) figure to `Money` in integer minor units, banker-safe by
    rounding to the nearest penny. Requires the assumption ref — a currency figure is never bare."""
    return Money(
        amount_minor=round(pounds * 100),
        currency=currency,
        assumption_register_ref=ref,
    )


def _npv_pounds(
    annual_cashflow: float, discount_rate: float, horizon_years: int, risk_factor: float
) -> float:
    """Risk-adjusted NPV of a level annual cash flow over the horizon: Σ_{t=1..H}
    (cashflow · risk) / (1+r)^t. Risk factor (a probability/confidence in [0,1]) discounts for the
    chance the lever does not fully land — the §10 'risk-adjusted' qualifier."""
    if not (0.0 <= risk_factor <= 1.0):
        raise ValueError(f"risk_factor is a probability in [0,1], got {risk_factor}.")
    if horizon_years < 1:
        raise ValueError(f"horizon_years must be ≥ 1, got {horizon_years}.")
    if discount_rate <= -1.0:
        raise ValueError(f"discount_rate must be > -1, got {discount_rate}.")
    return sum(
        (annual_cashflow * risk_factor) / (1.0 + discount_rate) ** t
        for t in range(1, horizon_years + 1)
    )


# --- Layer 1: cost ----------------------------------------------------------------------


def cost_estimate(
    *,
    effort_days: float,
    day_rate: float,
    currency: Currency,
    primary_ref: str,
    assumption_refs: Sequence[str],
    note: str | None = None,
) -> CostEstimate:
    """Hard upgrade cost = effort × day-rate, in currency (layer 1)."""
    total = _pounds_to_money(effort_days * day_rate, currency, primary_ref)
    return CostEstimate(total=total, assumption_refs=tuple(assumption_refs), note=note)


# --- Layer 2: the four evidenced levers -------------------------------------------------


def cost_to_serve_lever(
    *,
    cost_to_serve_per_client: float,
    active_clients: float,
    reduction_fraction: float,
    discount_rate: float,
    horizon_years: int,
    adoption_probability: float,
    currency: Currency,
    primary_ref: str,
    assumption_refs: Sequence[str],
    note: str | None = None,
) -> LeverValuation:
    """Cost-to-serve saving: the upgrade cuts per-client servicing cost across the client base."""
    annual = cost_to_serve_per_client * active_clients * reduction_fraction
    npv = _npv_pounds(annual, discount_rate, horizon_years, adoption_probability)
    return LeverValuation(
        lever=LeverKind.COST_TO_SERVE,
        npv=_pounds_to_money(npv, currency, primary_ref),
        assumption_refs=tuple(assumption_refs),
        note=note,
    )


def project_drag_lever(
    *,
    annual_delivery_spend: float,
    drag_fraction: float,
    reduction_fraction: float,
    discount_rate: float,
    horizon_years: int,
    adoption_probability: float,
    currency: Currency,
    primary_ref: str,
    assumption_refs: Sequence[str],
    note: str | None = None,
) -> LeverValuation:
    """Project drag: tech debt taxes delivery (McKinsey ~10–20%); the upgrade recovers a slice."""
    annual = annual_delivery_spend * drag_fraction * reduction_fraction
    npv = _npv_pounds(annual, discount_rate, horizon_years, adoption_probability)
    return LeverValuation(
        lever=LeverKind.PROJECT_DRAG,
        npv=_pounds_to_money(npv, currency, primary_ref),
        assumption_refs=tuple(assumption_refs),
        note=note,
    )


def incident_expected_loss_lever(
    *,
    annual_incident_expected_loss: float,
    reduction_fraction: float,
    discount_rate: float,
    horizon_years: int,
    adoption_probability: float,
    currency: Currency,
    primary_ref: str,
    assumption_refs: Sequence[str],
    note: str | None = None,
) -> LeverValuation:
    """Incident expected loss: P(incident) × cost; the upgrade lowers frequency/severity."""
    annual = annual_incident_expected_loss * reduction_fraction
    npv = _npv_pounds(annual, discount_rate, horizon_years, adoption_probability)
    return LeverValuation(
        lever=LeverKind.INCIDENT_EXPECTED_LOSS,
        npv=_pounds_to_money(npv, currency, primary_ref),
        assumption_refs=tuple(assumption_refs),
        note=note,
    )


def revenue_enablement_lever(
    *,
    enabled_annual_revenue: float,
    contribution_margin: float,
    discount_rate: float,
    horizon_years: int,
    realisation_probability: float,
    currency: Currency,
    primary_ref: str,
    assumption_refs: Sequence[str],
    note: str | None = None,
) -> LeverValuation:
    """Revenue enablement: capacity/time-to-market the upgrade unlocks, valued at contribution
    margin and risk-adjusted for the chance the revenue actually materialises."""
    annual = enabled_annual_revenue * contribution_margin
    npv = _npv_pounds(annual, discount_rate, horizon_years, realisation_probability)
    return LeverValuation(
        lever=LeverKind.REVENUE_ENABLEMENT,
        npv=_pounds_to_money(npv, currency, primary_ref),
        assumption_refs=tuple(assumption_refs),
        note=note,
    )


# --- Layer 3: strategic (ordinal) -------------------------------------------------------


def strategic_rating(dimension: str, rating: StrengthRating, rationale: str) -> StrategicRating:
    """A moat/durability implication as an ordinal rating — never priced in currency (layer 3)."""
    return StrategicRating(dimension=dimension, rating=rating, rationale=rationale)


# --- Rendering --------------------------------------------------------------------------


def render_assumption_register(register: AssumptionRegister) -> str:
    """Render the assumption register as a readable Markdown table — every currency figure in a
    deliverable traces to a row here (Methodology §10). Takes no Score and no Money."""
    lines = [
        "| Ref | Baseline | Unit | Source | Description |",
        "|---|---|---|---|---|",
    ]
    for a in register.entries:
        lines.append(
            f"| {a.ref} | {a.baseline_value:g} | {a.unit} | {a.source} | {a.description} |"
        )
    return "\n".join(lines)
