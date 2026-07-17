"""Product commission carrots (GRS-0123) — the live "how much you earn" figure for each Stream-A
product, resolved from the Earnings v7 schedule (ADR-0026).

The rate is read from the live `CommissionConfig`, never re-typed into course content, so the carrot
cannot drift from the real schedule. The worked example applies `compute_product_commission` to one
illustrative deal so an advisor sees a concrete pound figure alongside the percentage.
"""

from __future__ import annotations

from bcap_contracts.commissions import CommissionConfig, ProductCommissionCarrot
from bcap_contracts.money import Currency, Money

from grassmarket.earnings.commission import compute_product_commission

# An illustrative first-year deal the worked example prices — a teaching figure, not a forecast. It
# is £100,000 (in pence); the rate is the real carrot, the £ example just makes it concrete.
_EXAMPLE_DEAL_MINOR = 10_000_000
_EXAMPLE_REF = "grs-0123:illustrative-example-deal"


def _example_deal(currency: Currency) -> Money:
    return Money(
        amount_minor=_EXAMPLE_DEAL_MINOR,
        currency=currency,
        assumption_register_ref=_EXAMPLE_REF,
    )


def product_commission_carrot(
    product_id: str, config: CommissionConfig, *, example_deal: Money | None = None
) -> ProductCommissionCarrot:
    """The live carrot for one product. Fails loud on an unknown product (ADR-0001, via
    `require_product`). The worked example defaults to the illustrative deal in config currency."""
    product = config.require_product(product_id)  # fail loud on unknown product
    example = example_deal if example_deal is not None else _example_deal(config.currency)
    return ProductCommissionCarrot(
        product_id=product_id,
        name=product.name,
        yr1_bps=product.yr1_bps,
        yr2_bps=product.yr2_bps,
        window_months=product.window_months,
        example_deal=example,
        yr1_commission=compute_product_commission(example, product_id, 1, config),
        yr2_commission=compute_product_commission(example, product_id, 2, config),
        schedule_version=config.version,
    )


def all_product_carrots(
    config: CommissionConfig, *, example_deal: Money | None = None
) -> list[ProductCommissionCarrot]:
    """Every catalogue product's live carrot, in stable product_id order."""
    return [
        product_commission_carrot(pid, config, example_deal=example_deal)
        for pid in sorted(config.products)
    ]
