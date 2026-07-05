"""Value-bridge tests (GRS-0006, §10) — currency + ordinal, never a Score in the same equation.

A worked Meridian example: an assumption register of client-supplied baselines, a cost, the four
evidenced levers, and strategic ratings, assembled into a `ValueBridge`. Proves traceability is
enforced, the strategic layer is ordinal, and Money only ever combines with Money.
"""

from __future__ import annotations

import pytest
from bcap_contracts.common import StrengthRating
from bcap_contracts.money import Currency, Money
from bcap_contracts.value import (
    Assumption,
    AssumptionRegister,
    LeverKind,
    ValueBridge,
)
from pydantic import ValidationError

from grassmarket.value import (
    cost_estimate,
    cost_to_serve_lever,
    incident_expected_loss_lever,
    project_drag_lever,
    render_assumption_register,
    revenue_enablement_lever,
    strategic_rating,
)

_GBP = Currency.GBP


def _register() -> AssumptionRegister:
    return AssumptionRegister(
        entries=(
            Assumption(
                ref="AR-EFFORT",
                description="Back-office remediation effort",
                baseline_value=180,
                unit="person-days",
                source="Delivery estimate, Meridian CTO workshop",
            ),
            Assumption(
                ref="AR-RATE",
                description="Blended day rate",
                baseline_value=900,
                unit="GBP/day",
                source="Meridian vendor rate card FY26",
            ),
            Assumption(
                ref="AR-CTS",
                description="Cost to serve per active client",
                baseline_value=140,
                unit="GBP/yr",
                source="Meridian management accounts FY25",
            ),
            Assumption(
                ref="AR-CLIENTS",
                description="Active clients",
                baseline_value=180_000,
                unit="count",
                source="Meridian KPI pack FY25",
            ),
            Assumption(
                ref="AR-DELIVERY",
                description="Annual delivery spend",
                baseline_value=12_000_000,
                unit="GBP/yr",
                source="Meridian technology budget FY26",
            ),
            Assumption(
                ref="AR-INCIDENT",
                description="Annual incident expected loss",
                baseline_value=2_500_000,
                unit="GBP/yr",
                source="Meridian risk register FY25",
            ),
            Assumption(
                ref="AR-REVENUE",
                description="Revenue enabled by faster settlement",
                baseline_value=6_000_000,
                unit="GBP/yr",
                source="Meridian commercial model (client-supplied)",
            ),
        )
    )


def _bridge() -> ValueBridge:
    reg = _register()
    cost = cost_estimate(
        effort_days=180,
        day_rate=900,
        currency=_GBP,
        primary_ref="AR-EFFORT",
        assumption_refs=["AR-EFFORT", "AR-RATE"],
        note="Back-office remediation.",
    )
    levers = (
        cost_to_serve_lever(
            cost_to_serve_per_client=140,
            active_clients=180_000,
            reduction_fraction=0.08,
            discount_rate=0.10,
            horizon_years=5,
            adoption_probability=0.7,
            currency=_GBP,
            primary_ref="AR-CTS",
            assumption_refs=["AR-CTS", "AR-CLIENTS"],
        ),
        project_drag_lever(
            annual_delivery_spend=12_000_000,
            drag_fraction=0.15,
            reduction_fraction=0.25,
            discount_rate=0.10,
            horizon_years=5,
            adoption_probability=0.6,
            currency=_GBP,
            primary_ref="AR-DELIVERY",
            assumption_refs=["AR-DELIVERY"],
        ),
        incident_expected_loss_lever(
            annual_incident_expected_loss=2_500_000,
            reduction_fraction=0.40,
            discount_rate=0.10,
            horizon_years=5,
            adoption_probability=0.5,
            currency=_GBP,
            primary_ref="AR-INCIDENT",
            assumption_refs=["AR-INCIDENT"],
        ),
        revenue_enablement_lever(
            enabled_annual_revenue=6_000_000,
            contribution_margin=0.55,
            discount_rate=0.10,
            horizon_years=5,
            realisation_probability=0.4,
            currency=_GBP,
            primary_ref="AR-REVENUE",
            assumption_refs=["AR-REVENUE"],
        ),
    )
    strategic = (
        strategic_rating(
            "Moat durability",
            StrengthRating.ESTABLISHED,
            "Custody + settlement reliability deepens switching costs over a 3–5 year horizon.",
        ),
    )
    return ValueBridge(
        subject="Meridian Securities — Back Office remediation",
        assumption_register=reg,
        cost=cost,
        levers=levers,
        strategic=strategic,
    )


def test_worked_bridge_constructs_and_totals_in_money() -> None:
    bridge = _bridge()
    assert {lever.lever for lever in bridge.levers} == set(LeverKind)
    total = bridge.total_lever_npv()
    assert isinstance(total, Money)
    assert total.currency is _GBP
    assert total.amount_minor > 0  # the levers net positive on Meridian
    # Cost is its own Money in its own layer — never netted against the score domain.
    assert isinstance(bridge.cost.total, Money)


def test_every_figure_traces_to_the_register() -> None:
    # A lever citing an assumption that is not in the register must refuse to construct (§10).
    reg = _register()
    good = _bridge()
    orphan_lever = incident_expected_loss_lever(
        annual_incident_expected_loss=1_000_000,
        reduction_fraction=0.3,
        discount_rate=0.1,
        horizon_years=3,
        adoption_probability=0.5,
        currency=_GBP,
        primary_ref="AR-DOES-NOT-EXIST",
        assumption_refs=["AR-DOES-NOT-EXIST"],
    )
    with pytest.raises(ValidationError):
        ValueBridge(
            subject="broken",
            assumption_register=reg,
            cost=good.cost,
            levers=(orphan_lever,),
            strategic=good.strategic,
        )


def test_strategic_layer_is_ordinal_not_currency() -> None:
    bridge = _bridge()
    for rating in bridge.strategic:
        assert isinstance(rating.rating, StrengthRating)  # ordinal enum, never a decimal


def test_money_still_needs_currency_and_assumption_ref() -> None:
    with pytest.raises(ValidationError):
        Money(amount_minor=100, currency=_GBP, assumption_register_ref="")


def test_assumption_register_renders_every_baseline() -> None:
    rendered = render_assumption_register(_register())
    for a in _register().entries:
        assert a.ref in rendered
        assert a.source in rendered


def test_total_lever_npv_refuses_cross_currency() -> None:
    # Money.add refuses silent FX — the value bridge can never blend GBP and USD levers.
    gbp = Money(amount_minor=100, currency=Currency.GBP, assumption_register_ref="AR-1")
    usd = Money(amount_minor=100, currency=Currency.USD, assumption_register_ref="AR-2")
    with pytest.raises(ValueError):
        gbp.add(usd)
