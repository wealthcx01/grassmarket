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


def compute_engagement_commission(
    base_value: Money,
    tier: ConsultantTier,
    attribution: SourcingAttribution,
    config: CommissionConfig,
) -> Money:
    """The commission on an engagement of `base_value`, at the (tier, attribution) rate from config.

    ``amount = base_value × rate_bps / 10_000`` in integer minor units, rounded to the nearest minor
    unit with **half-to-even** (banker's rounding). The division is done in **pure integer
    arithmetic** — money is never denominated by a float (money.py invariant), so the figure is
    exact at every magnitude, not just realistic ones. The result carries the config `rate_ref` as
    its assumption reference, so the £ is never bare. The base value's currency must match the
    config currency — a mismatch is refused, never silently converted (no FX; ADR-0002)."""
    if base_value.currency is not config.currency:
        raise ValueError(
            f"Refusing to price a {base_value.currency.value} engagement under a "
            f"{config.currency.value} commission schedule: no silent FX."
        )
    if base_value.amount_minor < 0:
        raise ValueError("A contract value cannot be negative.")
    bps = config.rate_bps_for(tier, attribution)
    # Exact integer round-half-to-even: quotient, then bump on a strict-over-half remainder, or on
    # an exact half only when the quotient is odd. No float ever touches the money figure.
    quotient, remainder = divmod(base_value.amount_minor * bps, 10_000)
    if 2 * remainder > 10_000 or (2 * remainder == 10_000 and quotient % 2 == 1):
        quotient += 1
    amount_minor = quotient
    return Money(
        amount_minor=amount_minor,
        currency=config.currency,
        assumption_register_ref=config.rate_ref(tier, attribution),
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
