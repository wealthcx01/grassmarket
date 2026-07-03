"""Earnings / commission lines (PRD §7). Rates are configuration, never code — this contract
carries the *computed* amount as `Money`; the percentage that produced it lives in config."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import ConfigDict, Field

from bcap_contracts.base import OwnedResource
from bcap_contracts.money import Money


class CommissionKind(StrEnum):
    ENGAGEMENT = "engagement"
    WORKSHOP_RECOVERY_FEE = "workshop_recovery_fee"
    RETAINER = "retainer"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    INVOICED = "invoiced"
    PAID = "paid"


class CommissionLine(OwnedResource):
    model_config = ConfigDict(extra="forbid")

    engagement_id: UUID | None = None
    kind: CommissionKind
    amount: Money = Field(
        description="Computed commission amount (currency; assumptions attached)."
    )
    payment_status: PaymentStatus = PaymentStatus.PENDING
