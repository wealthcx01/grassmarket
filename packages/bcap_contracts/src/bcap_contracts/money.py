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
    # HC-005: the hub's record reaches counterparties these three do not cover. Bruntsfield Capital
    # Limited is incorporated in Hong Kong, and one advisory counterparty is a Swiss company. Both
    # invoice in USD today, so nothing needs these yet - they are here because a closed enum means
    # a code change and a release to raise an invoice in a currency somebody has already agreed to,
    # and that is a bad moment to discover the constraint.
    CHF = "CHF"
    HKD = "HKD"


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


class RecordedAmount(BaseModel):
    """An amount that is a FACT on a document, not a figure under assumptions (HC-005).

    ``Money`` above cannot be constructed without an ``assumption_register_ref``, and that is
    correct for what it is for: a lever NPV or a remediation cost is only meaningful under stated
    assumptions, and ADR-0002 exists because the prototype subtracted pounds from score-points.

    Holy Corner needs the other kind. ``USD 5,000`` on invoice INV-001 is not modelled, not
    uncertain and not an assumption. It is written on a document somebody signed. Putting it in a
    field named ``assumption_register_ref`` would say the opposite of what is true, and a field used
    against its own name is how a wrong number survives review: the next reader believes the name.

    So the two types are distinguished by WHERE THE NUMBER CAME FROM, which is the thing that
    actually differs:

    * ``Money`` cites the assumptions that justify a modelled figure.
    * ``RecordedAmount`` cites the source it was read from - a contract clause, an invoice, a
      partner's cash report, a bank statement line.

    Both are integer minor units with an explicit currency, and neither can exist without
    provenance. Neither converts to the other, and this package defines no function that takes one
    and returns the other: a modelled figure and an observed one are not interchangeable just
    because both are denominated in pounds.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    amount_minor: int = Field(
        description="Amount in integer minor units (e.g. cents). Never a float: a float cannot "
        "hold 0.1 exactly, and a commission recomputed on one drifts every time."
    )
    currency: Currency
    source_ref: str = Field(
        min_length=1,
        description="Where this amount was read from, precisely enough for somebody to check it "
        "against the document: a contract clause, an invoice number, a statement line. Mandatory, "
        "for the same reason Money's assumption reference is: an amount with no provenance is a "
        "claim, and this record exists to hold facts.",
    )

    @model_validator(mode="after")
    def _require_source(self) -> RecordedAmount:
        if not self.source_ref.strip():
            raise ValueError(
                "RecordedAmount requires a source_ref naming where the figure was read from. "
                "An amount nobody can trace back to a document is not a record of anything."
            )
        return self
