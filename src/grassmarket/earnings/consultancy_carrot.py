"""Consultancy commission carrots (GRS-0187) — the live "how much you earn" figure for each
Stream-B matrix cell, resolved from the Earnings v7 schedule (ADR-0026).

Structured exactly like `product_carrot.py`, for the same reason: the rate is read from the live
`CommissionConfig` and never re-typed into copy, so what an advisor is shown cannot drift from what
they are actually paid. The worked example applies `compute_consultancy_commission` to one
illustrative engagement so a percentage arrives with a concrete pound figure beside it.
"""

from __future__ import annotations

from bcap_contracts.commissions import (
    V7_SOURCING,
    CommissionConfig,
    ConsultancyCommissionCarrot,
    DeliveryType,
    SourcingAttribution,
)
from bcap_contracts.money import Currency, Money

from grassmarket.earnings.commission import compute_consultancy_commission

# The same £100,000 teaching figure the product carrot uses, so the two cards are comparable at a
# glance. A distinct ref keeps the provenance honest about which ticket introduced it.
_EXAMPLE_DEAL_MINOR = 10_000_000
_EXAMPLE_REF = "grs-0187:illustrative-example-deal"

# Human wording lives here, with the rate, rather than being typed into the UI — so a label and the
# number it describes cannot be changed independently of each other.
_DELIVERY_LABEL: dict[DeliveryType, str] = {
    DeliveryType.BRUNTSFIELD_LED: "Bruntsfield-led",
    DeliveryType.CONSULTANT_LED: "Consultant-led",
}
_SOURCING_LABEL: dict[SourcingAttribution, str] = {
    SourcingAttribution.SELF_SOURCED: "Self-sourced",
    SourcingAttribution.FIRM_SOURCED: "Firm-sourced",
    SourcingAttribution.BRUNTSFIELD_SOURCED: "Firm-sourced (legacy)",
    SourcingAttribution.CO_SOURCED: "Co-sourced (legacy)",
}


def _example_deal(currency: Currency) -> Money:
    return Money(
        amount_minor=_EXAMPLE_DEAL_MINOR,
        currency=currency,
        assumption_register_ref=_EXAMPLE_REF,
    )


def consultancy_commission_carrot(
    delivery_type: DeliveryType,
    sourcing: SourcingAttribution,
    config: CommissionConfig,
    *,
    example_deal: Money | None = None,
) -> ConsultancyCommissionCarrot:
    """The live carrot for one matrix cell. Fails loud on an unknown cell (via
    `require_consultancy_rate`), rather than presenting a rate nobody agreed."""
    rate = config.require_consultancy_rate(delivery_type, sourcing)
    example = example_deal if example_deal is not None else _example_deal(config.currency)
    return ConsultancyCommissionCarrot(
        delivery_type=delivery_type,
        sourcing=sourcing,
        delivery_label=_DELIVERY_LABEL[delivery_type],
        sourcing_label=_SOURCING_LABEL[sourcing],
        yr1_bps=rate.yr1_bps,
        thereafter_bps=rate.thereafter_bps,
        example_deal=example,
        yr1_commission=compute_consultancy_commission(example, sourcing, delivery_type, 1, config),
        # Year 2 is the first year of the "thereafter" period, which is ongoing and uncapped.
        thereafter_commission=compute_consultancy_commission(
            example, sourcing, delivery_type, 2, config
        ),
        schedule_version=config.version,
    )


def all_consultancy_carrots(
    config: CommissionConfig, *, example_deal: Money | None = None
) -> list[ConsultancyCommissionCarrot]:
    """Every cell of the v7 matrix, in a fixed order.

    Iterating the enums rather than listing the four cells means a new delivery model or sourcing
    axis surfaces on the earnings page automatically instead of being silently missing.
    """
    return [
        consultancy_commission_carrot(delivery, sourcing, config, example_deal=example_deal)
        for delivery in DeliveryType
        for sourcing in V7_SOURCING
    ]
