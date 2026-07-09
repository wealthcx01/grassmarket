"""Recovery-fee attribution — where Money enters the pipeline (GRS-0012, PRD §4).

The Workshop Recovery Fee: a workshop is delivered, the prospect contracts within a 12-month
attribution window, and the consultant earns a tier-dependent fee. Two invariants make this safe:

- **Rates are configuration, never code.** The per-tier fee and the attribution window live in
  ``registry_data/recovery_fees.yaml``, loaded fail-loud: every consultant tier must have a fee or
  the config refuses to load. Changing the fee is a config edit, never a code change.
- **The £ is always `Money`.** A fee has a currency and an ``assumption_register_ref`` naming the
  config that justifies it (a bare currency figure is unconstructible — GRS-0006). No value in this
  module is ever a Score; Money only combines with Money (ADR-0002).

The attribution record itself is **append-only, immutable, and content-hashed** — the scoring-run
pattern (CLAUDE.md non-negotiable #6): it cites the rate reference and window it used, so the fee is
reproducible and tamper-evident.
"""

from __future__ import annotations

import functools
from datetime import date
from importlib import resources
from typing import Any
from uuid import UUID

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from bcap_contracts.base import OwnedResource
from bcap_contracts.common import ConsultantTier
from bcap_contracts.money import Currency, Money


class RecoveryFeeError(Exception):
    """Base class for recovery-fee failures. Never swallowed."""


class RecoveryFeeConfigError(RecoveryFeeError):
    """The recovery-fee configuration is incomplete or malformed. Load-time refusal (fail loud)."""


class RecoveryFeeConfig(BaseModel):
    """The recovery-fee schedule — the attribution window plus a per-tier fee. Every consultant
    tier must be present (ADR-0001 completeness); a missing tier is a refusal, never a default."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = Field(min_length=1)
    currency: Currency
    attribution_window_days: int = Field(ge=1, description="The 12-month attribution window.")
    tier_fees_minor: dict[ConsultantTier, int] = Field(
        description="Fee per consultant tier, in integer minor units (e.g. pence)."
    )

    @model_validator(mode="after")
    def _require_every_tier(self) -> RecoveryFeeConfig:
        missing = set(ConsultantTier) - set(self.tier_fees_minor)
        if missing:
            shown = ", ".join(t.value for t in sorted(missing))
            raise RecoveryFeeConfigError(
                f"recovery_fees.yaml is incomplete — no fee for tier(s): {shown}. Every consultant "
                f"tier must have a configured fee (no defaults — ADR-0001)."
            )
        for tier, minor in self.tier_fees_minor.items():
            if minor < 0:
                raise RecoveryFeeConfigError(f"Fee for {tier.value} is negative ({minor}).")
        return self

    def rate_ref(self, tier: ConsultantTier) -> str:
        """The assumption-register reference a fee at this tier derives from — the config that
        justifies the figure (Money is never bare)."""
        return f"{self.version}:{tier.value}"

    def fee_for(self, tier: ConsultantTier) -> Money:
        """The recovery fee for a consultant tier, as `Money` carrying its config reference. Fail
        loud on an unconfigured tier rather than defaulting."""
        try:
            minor = self.tier_fees_minor[tier]
        except KeyError as exc:  # pragma: no cover - guarded by the completeness validator
            raise RecoveryFeeConfigError(
                f"No recovery fee configured for tier {tier.value}."
            ) from exc
        return Money(
            amount_minor=minor, currency=self.currency, assumption_register_ref=self.rate_ref(tier)
        )


def _load_yaml(filename: str) -> Any:
    data_pkg = resources.files("bcap_contracts").joinpath("registry_data")
    with resources.as_file(data_pkg.joinpath(filename)) as path:
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)


@functools.lru_cache(maxsize=1)
def load_recovery_fee_config() -> RecoveryFeeConfig:
    """Load + validate the recovery-fee config once. Fails loud on an incomplete/malformed file."""
    raw = _load_yaml("recovery_fees.yaml")
    if not isinstance(raw, dict):
        raise RecoveryFeeConfigError("recovery_fees.yaml must be a mapping.")
    return RecoveryFeeConfig.model_validate(raw)


class RecoveryFeeAttribution(OwnedResource):
    """An immutable, content-hashed record that a delivered workshop was attributed a recovery fee
    because its prospect contracted within the window. Append-only — never updated once written."""

    model_config = ConfigDict(extra="forbid")

    workshop_id: UUID
    prospect_id: UUID
    delivered_on: date
    contracted_on: date
    window_days: int = Field(ge=1, description="The attribution window this record used (config).")
    rate_ref: str = Field(
        min_length=1, description="The config rate reference the fee derives from."
    )
    fee: Money = Field(description="The computed recovery fee (currency; assumptions attached).")
    content_hash: str = Field(
        min_length=1, description="SHA-256 immutability seal over the record."
    )
