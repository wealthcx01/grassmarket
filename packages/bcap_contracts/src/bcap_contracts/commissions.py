"""Earnings / commission lines + the commission-rate schedule (PRD §7; v7 per ADR-0026).

Rates are **configuration, never code**, loaded fail-loud from ``registry_data/commissions.yaml``:
a gap in either stream refuses to load — no defaults (ADR-0001 completeness). Commission Schedule
**v7** is a **two-stream** model:

- **Stream A — product commission:** per product ``{yr1_bps, yr2_bps, window_months}`` on cash
  received under a qualifying deal; past the window the rate is zero.
- **Stream B — consultancy commission:** a ``delivery_type × sourcing`` matrix of
  ``{yr1_bps, thereafter_bps}``, uncapped ongoing share-of-outcome.

The £ is always `Money`, carrying the config reference that justifies it (ADR-0002); a recorded line
cites the ``rate_ref`` it used, so a later rate change is **never retroactive** (the scoring-run
immutability pattern, non-negotiable #6).

Sourcing reconciliation (ADR-0026): v7's axes are **self / firm** (firm = the Bruntsfield funnel /
inbound). The pre-v7 ``bruntsfield_sourced`` / ``co_sourced`` values are **retained** as legacy enum
members so historical v1 lines still validate, and both fold into ``firm_sourced`` for v7 pricing —
they are not v7 matrix keys.
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


class CommissionStream(StrEnum):
    """The two v7 commission streams (ADR-0026)."""

    PRODUCT = "product"  # Stream A
    CONSULTANCY = "consultancy"  # Stream B


class SourcingAttribution(StrEnum):
    """Who sourced the deal. v7 axes are SELF / FIRM; the two legacy values are retained for
    historical lines and fold into FIRM for v7 pricing (ADR-0026)."""

    SELF_SOURCED = "self_sourced"
    FIRM_SOURCED = "firm_sourced"  # v7: the Bruntsfield funnel / inbound
    BRUNTSFIELD_SOURCED = "bruntsfield_sourced"  # legacy (pre-v7)
    CO_SOURCED = "co_sourced"  # legacy (pre-v7)


class DeliveryType(StrEnum):
    """The consultancy delivery model (ADR-0026), mirroring SourcingAttribution's shape."""

    BRUNTSFIELD_LED = "bruntsfield_led"  # Power Platform Assessment / methodology work
    CONSULTANT_LED = "consultant_led"  # bespoke, client-/consultant-determined scope


# v7 matrix axes: the consultancy matrix keys on these two sourcing values only.
V7_SOURCING: tuple[SourcingAttribution, ...] = (
    SourcingAttribution.SELF_SOURCED,
    SourcingAttribution.FIRM_SOURCED,
)


class PaymentStatus(StrEnum):
    """Lifecycle of a commission line: earned (pending) → invoiced to Bruntsfield → paid out."""

    PENDING = "pending"
    INVOICED = "invoiced"
    PAID = "paid"


class CommissionConfigError(Exception):
    """The commission configuration is incomplete or malformed. Load-time refusal (fail loud)."""


class ProductRate(BaseModel):
    """Stream-A per-product rate: Year-1 / Year-2 bps + window (months) past which it is £0."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    yr1_bps: int = Field(ge=0)
    yr2_bps: int = Field(ge=0)
    window_months: int = Field(gt=0)


class ConsultancyRate(BaseModel):
    """Stream-B matrix cell: first-12-month bps and the thereafter (ongoing) bps."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    yr1_bps: int = Field(ge=0)
    thereafter_bps: int = Field(ge=0)


class ProductRef(BaseModel):
    """A reference to a Stream-A product in the catalogue — validated against the config's products
    map (fail loud on an unknown product_id, ADR-0001)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    product_id: str = Field(min_length=1)
    name: str = Field(min_length=1)


class CommissionConfig(BaseModel):
    """The v7 two-stream commission schedule. Every product must carry all three rate fields and
    every ``delivery_type × sourcing`` cell must be present — a gap is a load-time refusal, no
    defaults (ADR-0001)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = Field(min_length=1)
    currency: Currency
    # Stream A — product catalogue.
    products: dict[str, ProductRate] = Field(
        description="Stream-A product commission rates, keyed by product_id."
    )
    # Stream B — consultancy matrix: delivery_type → sourcing → rate.
    consultancy: dict[DeliveryType, dict[SourcingAttribution, ConsultancyRate]] = Field(
        description="Stream-B consultancy rates, keyed delivery_type × sourcing."
    )

    @model_validator(mode="after")
    def _require_completeness(self) -> CommissionConfig:
        # Stream A: at least one product; Field constraints already enforce non-negative/window.
        if not self.products:
            raise CommissionConfigError("commissions.yaml Stream A has no products.")
        # Stream B: every delivery_type × v7-sourcing cell present.
        for delivery in DeliveryType:
            by_sourcing = self.consultancy.get(delivery)
            if by_sourcing is None:
                raise CommissionConfigError(
                    f"commissions.yaml Stream B is missing delivery type {delivery.value}."
                )
            missing = set(V7_SOURCING) - set(by_sourcing)
            if missing:
                shown = ", ".join(s.value for s in sorted(missing))
                raise CommissionConfigError(
                    f"commissions.yaml Stream B: {delivery.value} is missing sourcing: {shown}."
                )
            stray = set(by_sourcing) - set(V7_SOURCING)
            if stray:
                shown = ", ".join(s.value for s in sorted(stray))
                raise CommissionConfigError(
                    f"commissions.yaml Stream B: {delivery.value} has non-v7 sourcing: {shown}."
                )
        return self

    # ------------------------------------------------------------------ Stream A accessors
    def require_product(self, product_id: str) -> ProductRate:
        """The product rate for `product_id`, or fail loud on an unknown product (ADR-0001)."""
        try:
            return self.products[product_id]
        except KeyError as exc:
            raise CommissionConfigError(
                f"No Stream-A product configured for product_id {product_id!r}."
            ) from exc

    def product_ref(self, product_id: str) -> ProductRef:
        """Resolve a `ProductRef` for a product, validated against the catalogue."""
        rate = self.require_product(product_id)
        return ProductRef(product_id=product_id, name=rate.name)

    def product_rate_ref(self, product_id: str, contract_year: int) -> str:
        """The assumption-register reference a Stream-A commission derives from."""
        return f"{self.version}:product:{product_id}:yr{contract_year}"

    # ------------------------------------------------------------------ Stream B accessors
    def require_consultancy_rate(
        self, delivery_type: DeliveryType, sourcing: SourcingAttribution
    ) -> ConsultancyRate:
        """The consultancy rate for a (delivery_type, sourcing) cell. Fail loud on unknown."""
        try:
            return self.consultancy[delivery_type][sourcing]
        except KeyError as exc:
            raise CommissionConfigError(
                f"No Stream-B rate configured for {delivery_type.value}/{sourcing.value}."
            ) from exc

    def consultancy_rate_ref(
        self, delivery_type: DeliveryType, sourcing: SourcingAttribution, period: str
    ) -> str:
        """The assumption-register reference a Stream-B commission derives from."""
        return f"{self.version}:consultancy:{delivery_type.value}:{sourcing.value}:{period}"


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
    """One earned commission — immutable once recorded. Provenance (tier/attribution/rate_ref/
    base_value for legacy; product_id/delivery_type/contract_year/window_end for v7) is stamped at
    record time, so a later rate change is never retroactive; the line reproduces from its own
    fields. `payment_status` is the one mutable field (its forward-only lifecycle)."""

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
    # v7 two-stream provenance (ADR-0026); null on legacy/recovery lines (non-retroactive).
    stream: CommissionStream | None = None
    product_id: str | None = None
    delivery_type: DeliveryType | None = None
    contract_year: int | None = Field(
        default=None, description="1 = Year 1, 2 = Year 2, 3+ = thereafter / post-window."
    )
    window_end: date | None = Field(
        default=None, description="Stream-A window cut-off; past it the product rate is zero."
    )
    client_paid_on: date | None = Field(
        default=None, description="Pay-when-paid anchor: the date the client cash was received."
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


class ProductCommissionCarrot(BaseModel):
    """The live "how much you earn" figure for a Stream-A product (GRS-0123) — the commission carrot
    on a product course. Resolved from the Earnings v7 schedule (never re-typed): the Year-1 and
    Year-2 rates come straight from the product's `ProductRate`, and the worked example is
    `compute_product_commission` applied to an illustrative deal. Stamped with `schedule_version` so
    the figure is never bare, exactly like `Money.assumption_register_ref` (ADR-0002)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    product_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    yr1_bps: int = Field(ge=0)
    yr2_bps: int = Field(ge=0)
    window_months: int = Field(gt=0)
    example_deal: Money = Field(description="The illustrative deal the worked example prices.")
    yr1_commission: Money = Field(
        description="Year-1 commission on the example deal (live compute)."
    )
    yr2_commission: Money = Field(
        description="Year-2 commission on the example deal (live compute)."
    )
    schedule_version: str = Field(
        min_length=1, description="The commission-config version stamped."
    )
