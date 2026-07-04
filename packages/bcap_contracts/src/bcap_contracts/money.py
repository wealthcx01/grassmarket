"""The `Money` type and the score/currency boundary — ADR-0002's structural guarantee.

The prototype computed `LV = κ·Δq/(1+r) − cost`, subtracting pounds from score-points. That
category error is made *unrepresentable* here: `Money` and `Score` are distinct types, and this
package defines **no** constructor, operator, or function that takes a score-domain value and a
`Money` and returns a number. Prioritisation lives in the score domain (ΔV, full re-scoring);
the value bridge prices in currency; the two sit side by side and are never divided one by the
other (ADR-0002 §2–§4).

Amounts are stored as **integer minor units** (pence/cents) so currency arithmetic within a
single currency is exact — floats never denominate money.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Currency(StrEnum):
    GBP = "GBP"
    USD = "USD"
    EUR = "EUR"


class Money(BaseModel):
    """A currency amount that cannot exist without an explicit currency and a reference to the
    assumption register that justifies it (Methodology §10, ADR-0002 compliance test).

    A lever NPV or remediation cost is only meaningful under stated assumptions; a `Money`
    without an ``assumption_register_ref`` is not constructible.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    amount_minor: int = Field(description="Amount in integer minor units (e.g. pence).")
    currency: Currency
    assumption_register_ref: str = Field(
        min_length=1,
        description="Reference to the assumption-register entry that justifies this figure. "
        "Mandatory: currency claims are never made without stated assumptions (Methodology §10).",
    )

    @model_validator(mode="after")
    def _require_assumptions(self) -> Money:
        # min_length=1 already guards empty; this makes the intent loud and explicit.
        if not self.assumption_register_ref.strip():
            raise ValueError(
                "Money requires a non-empty assumption_register_ref (ADR-0002): currency claims "
                "are never made without an assumption register."
            )
        return self

    def add(self, other: Money) -> Money:
        """Add two amounts in the SAME currency. Cross-currency arithmetic is refused loudly —
        there is no silent FX. Note this never touches a Score; it stays wholly in currency."""
        if other.currency is not self.currency:
            raise ValueError(
                f"Refusing to add {self.currency.value} and {other.currency.value}: no silent FX."
            )
        return Money(
            amount_minor=self.amount_minor + other.amount_minor,
            currency=self.currency,
            assumption_register_ref=f"{self.assumption_register_ref}+{other.assumption_register_ref}",
        )
