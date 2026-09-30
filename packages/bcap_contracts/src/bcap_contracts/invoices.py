"""Invoices, payments, receivable commission, and what things cost.

HC-005, plan D4 and D5. The money half of the group-level record.

Every amount here is a `RecordedAmount`: integer minor units, an explicit currency, and a reference
to the document it was read from. No amount in this module is modelled, so none of them is `Money`
(see `money.py` for why the two are different types and why neither converts to the other).

**Nothing here sums across currencies, ever.** There is no total field that could. An aggregate over
mixed currencies is computed per currency by the consumer and displayed per currency, because the
alternative is a single number that is not any amount of anything.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bcap_contracts.money import Currency, RecordedAmount
from bcap_contracts.organisations import Pillar


class InvoiceStatus(StrEnum):
    """Forward only, like the Advisory Studio's payment status. No skips and no reversals.

    `overdue` is deliberately NOT here. It is derived from the due date and the status every
    time it is asked for, because a stored "overdue" is a fact that was true when a job last ran.
    """

    DRAFT = "draft"
    ISSUED = "issued"
    SENT = "sent"
    PART_PAID = "part_paid"
    PAID = "paid"
    WRITTEN_OFF = "written_off"
    VOID = "void"


class InvoiceLine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str = Field(min_length=1)
    quantity: int = Field(default=1, gt=0)
    unit_amount: RecordedAmount
    tax_amount: RecordedAmount | None = None
    contract_term_ref: str | None = Field(
        default=None, description="The term this line is charging for, where there is one."
    )

    @model_validator(mode="after")
    def _tax_matches_currency(self) -> InvoiceLine:
        if self.tax_amount and self.tax_amount.currency != self.unit_amount.currency:
            raise ValueError(
                f"tax is in {self.tax_amount.currency} and the line is in "
                f"{self.unit_amount.currency}. Two currencies never meet in one sum (plan D5)."
            )
        return self


class Invoice(BaseModel):
    """What we billed, to whom, for what, and whether it has been paid."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    number: str = Field(min_length=1, description="The human number, e.g. 'INV-001'.")
    issuer_organisation_id: str = Field(min_length=1, description="The Bruntsfield entity billing.")
    billed_to_organisation_id: str = Field(min_length=1)
    contract_id: str | None = None
    contract_term_ref: str | None = None
    status: InvoiceStatus = InvoiceStatus.DRAFT
    issued_on: date | None = None
    due_on: date | None = None
    currency: Currency
    lines: tuple[InvoiceLine, ...] = ()
    total: RecordedAmount
    tax_total: RecordedAmount | None = None
    external_ref: str | None = Field(
        default=None, description="The id in whatever system issued it, e.g. a Wise invoice id."
    )

    @model_validator(mode="after")
    def _one_currency_throughout(self) -> Invoice:
        if self.total.currency != self.currency:
            raise ValueError(
                f"the invoice is in {self.currency} and its total is in {self.total.currency}"
            )
        for i, line in enumerate(self.lines, start=1):
            if line.unit_amount.currency != self.currency:
                raise ValueError(
                    f"line {i} is in {line.unit_amount.currency} and the invoice is in "
                    f"{self.currency}. An invoice is denominated in one currency."
                )
        return self

    @model_validator(mode="after")
    def _issued_invoices_have_dates(self) -> Invoice:
        if self.status is not InvoiceStatus.DRAFT and self.issued_on is None:
            raise ValueError(
                f"an invoice in status {self.status.value!r} has been issued, so issued_on "
                "is required. 'Overdue' is derived from a date, and there is none to derive from."
            )
        return self


class MatchedBy(StrEnum):
    """Who decided this payment pays that invoice."""

    AUTO = "auto"  # an exact reference match, still recorded as an event
    HUMAN = "human"


class Payment(BaseModel):
    """Money that arrived. Recorded after the fact; Holy Corner never moves any (plan D6)."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    invoice_id: str | None = Field(
        default=None, description="Absent for a receipt nobody has matched to an invoice yet."
    )
    received_on: date
    amount: RecordedAmount
    fx_rate: str | None = Field(
        default=None,
        description="The rate as a decimal string, where a conversion happened. A string and not a "
        "float: a rate is a recorded fact and must round-trip exactly (plan D5).",
    )
    fx_source: str | None = Field(default=None, description="Who published the rate, and when.")
    external_ref: str | None = None
    matched_by: MatchedBy | None = None

    @model_validator(mode="after")
    def _a_match_has_an_invoice_and_a_rate_has_a_source(self) -> Payment:
        if self.matched_by is not None and self.invoice_id is None:
            raise ValueError("a payment cannot be matched by anybody to no invoice")
        if bool(self.fx_rate) != bool(self.fx_source):
            raise ValueError(
                "an FX rate and its source travel together. A rate with no source is a number "
                "somebody typed (plan D5)."
            )
        return self


class ReceivableStatus(StrEnum):
    FORECAST = "forecast"
    DUE = "due"
    INVOICED = "invoiced"
    PAID = "paid"
    WRITTEN_OFF = "written_off"


class CommissionReceivable(BaseModel):
    """What a partner owes us for one reported tranche of their customer's cash.

    `contract_year` is the year OF THE ENGAGEMENT, counted from first cash received, not a calendar
    year and not a year of the agreement. Two rates apply depending on it, so a wrong year here is a
    wrong invoice.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    contract_id: str = Field(min_length=1)
    contract_term_ref: str | None = None
    customer_deal_ref: str | None = Field(
        default=None, description="The partner's own deal this commission arises from."
    )
    cash_received: RecordedAmount = Field(
        description="What the partner reported receiving from their customer."
    )
    contract_year: int = Field(ge=1, description="Counted from first cash received on the deal.")
    computed: RecordedAmount = Field(
        description="What we are owed on that cash, at the year's rate."
    )
    drawdown_applied: RecordedAmount | None = Field(
        default=None,
        description="Where a creditable commitment payment reduces this one, by how much.",
    )
    status: ReceivableStatus = ReceivableStatus.FORECAST
    basis: str = Field(
        min_length=1,
        description="How this figure was arrived at, in words a person can check against the "
        "contract: which rate, which window, which report. A computed number with no stated basis "
        "is one nobody can defend in an audit, and both advisory agreements grant an audit right.",
    )

    @model_validator(mode="after")
    def _one_currency_throughout(self) -> CommissionReceivable:
        if self.computed.currency != self.cash_received.currency:
            raise ValueError(
                f"commission is in {self.computed.currency} and the cash it is computed from is in "
                f"{self.cash_received.currency}"
            )
        if self.drawdown_applied and self.drawdown_applied.currency != self.computed.currency:
            raise ValueError("the drawdown and the commission must be in the same currency")
        return self


class CostCentre(BaseModel):
    """Where money goes, grouped so a pillar can have a profit and loss."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    pillar: Pillar
    organisation_id: str | None = Field(
        default=None,
        description="The venture or client this centre exists for, where there is one.",
    )
    contract_id: str | None = None


class ExpenseAllocation(StrEnum):
    """An expense is proposed against a cost centre and confirmed by a person, never assumed."""

    PROPOSED = "proposed"
    CONFIRMED = "confirmed"


class Expense(BaseModel):
    """Money out, allocated to a pillar.

    `counterparty` is stored REDACTED. Bank narratives cross the untrusted-content boundary and
    carry account references; what a profit and loss needs is who it was and what it cost, not the
    last four digits of anybody's card.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    cost_centre_id: str | None = Field(
        default=None, description="Absent until somebody confirms where it belongs."
    )
    category: str | None = None
    amount: RecordedAmount
    incurred_on: date
    counterparty: str | None = Field(
        default=None, description="Redacted at intake. Never a full account reference."
    )
    allocation: ExpenseAllocation = ExpenseAllocation.PROPOSED
    bank_activity_ref: str | None = None

    @model_validator(mode="after")
    def _confirmed_expenses_have_somewhere_to_go(self) -> Expense:
        if self.allocation is ExpenseAllocation.CONFIRMED and self.cost_centre_id is None:
            raise ValueError(
                "a confirmed expense needs a cost centre. Confirming an allocation to nowhere is "
                "how a cost disappears from every pillar's profit and loss at once."
            )
        return self
