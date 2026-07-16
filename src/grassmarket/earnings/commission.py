"""Commission computation + the immutability seal (GRS-0028, PRD §7).

Pure, deterministic helpers over an engagement commission: apply the config's basis-point rate to a
contract value, and hash the recorded line so it is tamper-evident and reproducible. The £ is
`Money` throughout, carrying the config reference that justifies it — nothing here is a Score
(ADR-0002). The rate is read from config, never hard-coded, and stamped onto the line via `rate_ref`
so a later config change is never retroactive.
"""

from __future__ import annotations

import hashlib
from datetime import date
from uuid import UUID

from bcap_contracts.commissions import (
    CommissionConfig,
    CommissionKind,
    CommissionStream,
    DeliveryType,
    SourcingAttribution,
)
from bcap_contracts.common import ConsultantTier
from bcap_contracts.money import Money


def _apply_bps(base_value: Money, bps: int, config: CommissionConfig, rate_ref: str) -> Money:
    """Apply a basis-point rate to a base value, exactly (reuses the GRS-0028 money discipline).

    ``amount = base_value × bps / 10_000`` in integer minor units, rounded to the nearest minor
    unit with **half-to-even** (banker's rounding). The division is **pure integer arithmetic** —
    money is never denominated by a float (money.py invariant), so the figure is exact at every
    magnitude. The result carries `rate_ref` so the £ is never bare. The base value's currency must
    match the config currency — a mismatch is refused, never converted (no FX; ADR-0002)."""
    if base_value.currency is not config.currency:
        raise ValueError(
            f"Refusing to price a {base_value.currency.value} amount under a "
            f"{config.currency.value} commission schedule: no silent FX."
        )
    if base_value.amount_minor < 0:
        raise ValueError("A contract value cannot be negative.")
    # Exact integer round-half-to-even: quotient, bump on a strict-over-half remainder, or on an
    # exact half only when the quotient is odd. No float ever touches the money figure.
    quotient, remainder = divmod(base_value.amount_minor * bps, 10_000)
    if 2 * remainder > 10_000 or (2 * remainder == 10_000 and quotient % 2 == 1):
        quotient += 1
    return Money(amount_minor=quotient, currency=config.currency, assumption_register_ref=rate_ref)


def compute_product_commission(
    base_value: Money, product_id: str, contract_year: int, config: CommissionConfig
) -> Money:
    """Stream A — product commission (ADR-0026). Year 1 uses the product's `yr1_bps`, Year 2 its
    `yr2_bps`; **Year 3+ (past the window) prices to exactly £0** — the model carries only two rate
    tiers, so nothing earns beyond Year 2. The caller supplies the year (the helper does not
    infer dates); an unknown product refuses loud (ADR-0001)."""
    if contract_year < 1:
        raise ValueError("contract_year is 1-based (Year 1 = the first 12 months).")
    product = config.require_product(product_id)  # fail loud on unknown product
    if contract_year == 1:
        bps = product.yr1_bps
    elif contract_year == 2:
        bps = product.yr2_bps
    else:
        bps = 0  # past the window: no Year-3+ rate exists → £0
    return _apply_bps(base_value, bps, config, config.product_rate_ref(product_id, contract_year))


def compute_consultancy_commission(
    base_value: Money,
    sourcing: SourcingAttribution,
    delivery_type: DeliveryType,
    contract_year: int,
    config: CommissionConfig,
) -> Money:
    """Stream B — consultancy commission (ADR-0026). The `delivery_type × sourcing` cell's `yr1_bps`
    applies in the first 12-month period (Year 1), `thereafter_bps` after — uncapped, ongoing
    share-of-outcome. The caller supplies the period as a 1-based contract year; an unknown cell
    refuses loud (ADR-0001)."""
    if contract_year < 1:
        raise ValueError("contract_year is 1-based (Year 1 = the first 12 months).")
    rate = config.require_consultancy_rate(delivery_type, sourcing)  # fail loud on unknown cell
    bps = rate.yr1_bps if contract_year == 1 else rate.thereafter_bps
    period = "yr1" if contract_year == 1 else "thereafter"
    return _apply_bps(
        base_value, bps, config, config.consultancy_rate_ref(delivery_type, sourcing, period)
    )


def commission_content_hash(
    *,
    owner_consultant_id: UUID,
    engagement_id: UUID | None,
    kind: CommissionKind,
    amount: Money,
    earned_on: date | None,
    tier: ConsultantTier | None,
    attribution: SourcingAttribution | None,
    rate_ref: str | None,
    base_value: Money | None,
    source_attribution_id: UUID | None,
    stream: CommissionStream | None = None,
    product_id: str | None = None,
    delivery_type: DeliveryType | None = None,
    contract_year: int | None = None,
    window_end: date | None = None,
) -> str:
    """SHA-256 over the canonical commission-line FINANCIAL fields — the immutability seal
    (scoring-run pattern). `payment_status` is deliberately EXCLUDED — it is the one mutable field
    (the pending → invoiced → paid lifecycle), so the seal protects the figures that must never
    change (amount, base value, rate, tier, attribution, and the v7 stream provenance) while the
    status advances freely. `client_paid_on` is EXCLUDED too (ADR-0026): it is a lifecycle
    precondition on advancing to `paid`, not a figure — like `payment_status`, it moves after record
    time. The four v7 provenance fields (product_id / delivery_type / contract_year / window_end)
    ARE sealed."""
    canonical = "|".join(
        [
            str(owner_consultant_id),
            str(engagement_id) if engagement_id else "-",
            kind.value,
            str(amount.amount_minor),
            amount.currency.value,
            amount.assumption_register_ref,
            earned_on.isoformat() if earned_on else "-",
            tier.value if tier else "-",
            attribution.value if attribution else "-",
            rate_ref or "-",
            str(base_value.amount_minor) if base_value else "-",
            base_value.currency.value if base_value else "-",
            base_value.assumption_register_ref if base_value else "-",
            str(source_attribution_id) if source_attribution_id else "-",
            stream.value if stream else "-",
            product_id or "-",
            delivery_type.value if delivery_type else "-",
            str(contract_year) if contract_year is not None else "-",
            window_end.isoformat() if window_end else "-",
        ]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
