"""Earnings / commission lines + the commission-rate schedule (PRD §7).

Rates are **configuration, never code** (per tier and sourcing attribution), loaded fail-loud from
``registry_data/commissions.yaml``: every tier × attribution must have a rate or the config refuses
to load — no defaults (ADR-0001 completeness). A commission is a percentage (basis points) of an
engagement's contract value; the £ is always `Money`, carrying the config reference that justifies
it (ADR-0002). A recorded commission cites the rate_ref it used, so a later rate change is **never
retroactive** — it reproduces exactly (the scoring-run immutability pattern, non-negotiable #6).
"""

from __future__ import annotations

import functools
from datetime import date
from enum import StrEnum
from importlib import resources
from typing import Any
from uuid import UUID

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from bcap_contracts.base import OwnedResource
from bcap_contracts.common import ConsultantTier
from bcap_contracts.money import Currency, Money


class CommissionKind(StrEnum):
    ENGAGEMENT = "engagement"
    WORKSHOP_RECOVERY_FEE = "workshop_recovery_fee"
    RETAINER = "retainer"


class SourcingAttribution(StrEnum):
    """Who sourced the deal — the second axis (with tier) of the commission rate (PRD §7)."""

    SELF_SOURCED = "self_sourced"
    BRUNTSFIELD_SOURCED = "bruntsfield_sourced"
    CO_SOURCED = "co_sourced"


class PaymentStatus(StrEnum):
    """Lifecycle of a commission line: earned (pending) → invoiced to Bruntsfield → paid out."""

    PENDING = "pending"
    INVOICED = "invoiced"
    PAID = "paid"


class CommissionConfigError(Exception):
    """The commission configuration is incomplete or malformed. Load-time refusal (fail loud)."""


class CommissionConfig(BaseModel):
    """The commission-rate schedule: a basis-point rate per (tier, attribution). Every combination
    must be present (ADR-0001 completeness); a missing one is a refusal, never a default."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = Field(min_length=1)
    currency: Currency
    rates_bps: dict[ConsultantTier, dict[SourcingAttribution, int]] = Field(
        description="Basis-point rate (100 bps = 1%) per consultant tier per sourcing attribution."
    )

    @model_validator(mode="after")
    def _require_every_combination(self) -> CommissionConfig:
        for tier in ConsultantTier:
            by_attr = self.rates_bps.get(tier)
            if by_attr is None:
                raise CommissionConfigError(
                    f"commissions.yaml is incomplete — no rates for tier {tier.value} "
                    f"(every tier × attribution must be configured; no defaults — ADR-0001)."
                )
            missing = set(SourcingAttribution) - set(by_attr)
            if missing:
                shown = ", ".join(a.value for a in sorted(missing))
                raise CommissionConfigError(
                    f"commissions.yaml: tier {tier.value} is missing attribution(s): {shown}."
                )
            for attr, bps in by_attr.items():
                if bps < 0:
                    raise CommissionConfigError(
                        f"Rate for {tier.value}/{attr.value} is negative ({bps} bps)."
                    )
        return self

    def rate_ref(self, tier: ConsultantTier, attribution: SourcingAttribution) -> str:
        """The assumption-register reference a commission at this tier/attribution derives from."""
        return f"{self.version}:{tier.value}:{attribution.value}"

    def rate_bps_for(self, tier: ConsultantTier, attribution: SourcingAttribution) -> int:
        """The basis-point rate for a (tier, attribution). Fail loud on an unconfigured pair."""
        try:
            return self.rates_bps[tier][attribution]
        except KeyError as exc:  # pragma: no cover - guarded by the completeness validator
            raise CommissionConfigError(
                f"No commission rate configured for {tier.value}/{attribution.value}."
            ) from exc


def _load_yaml(filename: str) -> Any:
    data_pkg = resources.files("bcap_contracts").joinpath("registry_data")
    with resources.as_file(data_pkg.joinpath(filename)) as path:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)


@functools.lru_cache(maxsize=1)
def load_commission_config() -> CommissionConfig:
    """Load + validate the commission config once. Fails loud on an incomplete/malformed file."""
    raw = _load_yaml("commissions.yaml")
    if not isinstance(raw, dict):
        raise CommissionConfigError("commissions.yaml must be a mapping.")
    return CommissionConfig.model_validate(raw)


class CommissionLine(OwnedResource):
    """One earned commission — immutable once recorded. For an engagement commission the provenance
    (tier, attribution, rate_ref, base_value) is stamped at record time, so a later rate change is
    never retroactive; the line reproduces from its own fields. `payment_status` is the one mutable
    field (its lifecycle), and it moves forward only (pending → invoiced → paid)."""

    model_config = ConfigDict(extra="forbid")

    engagement_id: UUID | None = None
    kind: CommissionKind
    amount: Money = Field(description="Computed commission amount (currency; assumptions attached)")
    payment_status: PaymentStatus = PaymentStatus.PENDING
    earned_on: date | None = None
    # Engagement-commission provenance (None for recovery-fee lines, which cite their attribution).
    tier: ConsultantTier | None = None
    attribution: SourcingAttribution | None = None
    rate_ref: str | None = None
    base_value: Money | None = Field(
        default=None, description="The contract value the rate was applied to."
    )
    source_attribution_id: UUID | None = Field(
        default=None, description="The recovery-fee attribution this line was claimed from, if any."
    )
    content_hash: str = Field(min_length=1, description="SHA-256 immutability seal over the line.")


class EarningsSummary(BaseModel):
    """An advisor's own earnings roll-up — self-scoped (the cross-advisor aggregate is Holy Corner
    scope, not this ticket). All monetary totals are `Money` in one currency."""

    model_config = ConfigDict(extra="forbid")

    owner_consultant_id: UUID
    currency: Currency
    ytd_earned: Money
    pending: Money
    invoiced: Money
    paid: Money
    projected_unpaid: Money = Field(
        description="Earned-but-unpaid (pending + invoiced) — the near-term projection."
    )
    line_count: int = Field(ge=0)
