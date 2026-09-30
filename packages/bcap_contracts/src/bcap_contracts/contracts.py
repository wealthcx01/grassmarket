"""Contracts, and their commercial terms as TYPED ROWS rather than prose.

HC-005, plan D4. This is the shape the whole of Holy Corner's Phase 1 stands on: a revenue engine
can only compute from terms it can read, and a term it cannot read is a PDF somebody has to open.

**Why terms are rows and not columns.** The obvious model gives `Contract` a `commission_rate`, a
`commitment_payment`, an `equity_split`. It breaks on the second contract. One advisory agreement
has two commission structures with different windows; a Foundry agreement has no commission at all
and has a milestone, an equity split and a long-stop instead; a consultant agreement has none of
those. Columns would mean most of them null on every row, and a fourth contract shape meaning a
migration. A `ContractTerm` is one typed row, a contract has as many as it has, and a new kind of
term is a new member of a union rather than an ALTER TABLE.

**Why a schedule is a contract.** A Master Services Agreement and its Engagement Schedule are two
documents with two dates and two signature blocks, and the schedule's terms override the MSA's for
what it covers. `parent_contract_id` says so, rather than flattening both into one record and
losing which document said what.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bcap_contracts.money import Currency, RecordedAmount
from bcap_contracts.organisations import Pillar


class ContractType(StrEnum):
    """The document kinds Bruntsfield actually signs. Every one of these exists on paper today."""

    MSA = "msa"
    ENGAGEMENT_SCHEDULE = "engagement_schedule"
    COLLABORATION_AGREEMENT = "collaboration_agreement"
    TERM_SHEET = "term_sheet"
    SERVICE_SCHEDULE = "service_schedule"
    CONSULTANT_AGREEMENT = "consultant_agreement"
    FOUNDERS_SERVICE_AGREEMENT = "founders_service_agreement"
    OTHER = "other"


class ContractStatus(StrEnum):
    """Forward only. A contract does not go back to draft once it has been signed."""

    DRAFT = "draft"
    SENT = "sent"
    SIGNED = "signed"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


# --------------------------------------------------------------------------- #
# The terms
# --------------------------------------------------------------------------- #
class CommissionRate(BaseModel):
    """What we earn on a deal, in basis points, per contract year.

    BASIS POINTS AND NOT A PERCENTAGE FLOAT. The Advisory Studio's own commission config is already
    in bps, the contracts are written in whole and half percents, and 7.5% is 750 - exact - where a
    float is 0.075 and is not. A rate that arrives as an integer and stays one cannot drift.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["commission_rate"] = "commission_rate"
    engagement_type: str = Field(
        min_length=1,
        description="Which kind of deal this rate applies to, in the contract's own words, "
        "e.g. 'white_label_exchange' or 'distribution_direct_acv'.",
    )
    yr1_bps: int = Field(ge=0, le=10_000, description="Year-one rate in basis points. 3000 is 30%.")
    yr2_bps: int = Field(
        ge=0, le=10_000, description="Year-two rate. 0 where year two earns nothing."
    )
    window_months: int = Field(
        gt=0,
        description="How long commission runs from first cash received on the engagement.",
    )


class CommitmentPayment(BaseModel):
    """A payment due on signature.

    `creditable` is the whole reason this is a field rather than an invoice line. Two counterparties
    each pay the same amount on signature and the two payments behave differently: one is
    non-refundable and NOT creditable against future commission, the other draws down against
    commission dollar for dollar until it is consumed. Getting that backwards overstates what we are
    owed by the whole amount, on a screen, to the person deciding whether to chase it.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["commitment_payment"] = "commitment_payment"
    amount: RecordedAmount
    creditable: bool = Field(
        description="True when the payment draws down against commission as it accrues; false when "
        "it is kept and commission is earned on top of it."
    )
    due_on_signature: bool = True


class RenewalRule(BaseModel):
    """What happens when the counterparty's own customer renews."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["renewal_rule"] = "renewal_rule"
    restarts_at_year_one: bool = Field(
        description="True where a renewal we materially contributed to restarts the window at "
        "year-one rates rather than continuing at year two."
    )
    material_contribution_presumed_months: int | None = Field(
        default=None,
        gt=0,
        description="Where the contract presumes material contribution from any documented contact "
        "within N months before renewal, N goes here. Absent means it must be argued.",
    )
    notice_days: int | None = Field(default=None, gt=0)


class RunOffPeriod(BaseModel):
    """How long commission keeps running after the agreement itself ends."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["run_off_period"] = "run_off_period"
    months: int = Field(gt=0)


class Milestone(BaseModel):
    """A thing that has to be true, not a payment.

    A Foundry venture earns nothing and is measured by whether it can support its founder. The
    threshold is a `RecordedAmount` when the measure is money and absent when it is not.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["milestone"] = "milestone"
    description: str = Field(min_length=1)
    measure: str = Field(
        min_length=1, description="What is measured, e.g. 'net_revenue_per_month'."
    )
    threshold: RecordedAmount | None = None
    sustained_months: int | None = Field(
        default=None,
        gt=0,
        description="How many consecutive periods the threshold must hold. A revenue figure hit "
        "once is not the same as one sustained, and the contract says which.",
    )


class EquitySplit(BaseModel):
    """Who holds what at spin-out, in basis points.

    `provisional` exists because the signed document has the figures in square brackets. Recording a
    bracketed placeholder as though it were agreed is how a negotiating position becomes a fact
    nobody remembers agreeing to.
    """

    model_config = ConfigDict(extra="forbid")

    kind: Literal["equity_split"] = "equity_split"
    holder: str = Field(min_length=1, description="'founder', 'bruntsfield', 'option_pool'.")
    bps: int = Field(ge=0, le=10_000, description="Basis points of the fully diluted total.")
    vesting_months: int | None = Field(default=None, gt=0)
    cliff_months: int | None = Field(default=None, gt=0)
    provisional: bool = Field(
        default=False,
        description="True where the signed document carries this figure in square brackets.",
    )

    @model_validator(mode="after")
    def _cliff_fits_inside_vesting(self) -> EquitySplit:
        if self.cliff_months and self.vesting_months and self.cliff_months > self.vesting_months:
            raise ValueError(
                f"a {self.cliff_months}-month cliff cannot sit inside {self.vesting_months} months "
                "of vesting"
            )
        return self


class LongStop(BaseModel):
    """The date by which something must have happened, or a stated remedy applies."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["long_stop"] = "long_stop"
    months: int = Field(gt=0)
    remedy: str | None = Field(
        default=None, description="What the counterparty may require if the date passes."
    )
    provisional: bool = False


class Restraint(BaseModel):
    """A non-compete or non-solicit, with its carve-outs."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["restraint"] = "restraint"
    restraint_type: str = Field(min_length=1, description="'non_compete' or 'non_solicit'.")
    months: int = Field(gt=0)
    carve_out: str | None = None
    provisional: bool = False


class PaymentTerms(BaseModel):
    """How long the counterparty has to pay, and in what."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["payment_terms"] = "payment_terms"
    days: int = Field(gt=0)
    currency: Currency
    method: str | None = Field(default=None, description="e.g. 'electronic_transfer'.")


ContractTerm = Annotated[
    CommissionRate
    | CommitmentPayment
    | RenewalRule
    | RunOffPeriod
    | Milestone
    | EquitySplit
    | LongStop
    | Restraint
    | PaymentTerms,
    Field(discriminator="kind"),
]
"""One commercial term. Discriminated on `kind`, so a term round-trips through JSON without a
consumer having to guess which shape it got back."""


class ContractDocument(BaseModel):
    """A file that IS the contract, or a version of it."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1, description="The version on the document, e.g. 'v6'.")
    document_kind: str = Field(
        min_length=1,
        description="'executed', 'draft', 'signed_counterparty' or 'countersigned'.",
    )
    storage_key: str = Field(min_length=1, description="Where the file lives. Never the file.")
    md5: str | None = Field(default=None, description="For refusing a duplicate upload.")


class Contract(BaseModel):
    """One signed (or unsigned) agreement.

    `dated_on` and `effective_on` are SEPARATE FIELDS AND BOTH ARE KEPT. One agreement in the record
    has a Master Services Agreement dated one day and a schedule stating it was entered into five
    weeks earlier. Collapsing them to a single date loses a discrepancy that is on the face of the
    documents and that somebody has to decide about; keeping both makes it visible every time the
    contract is read.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    type: ContractType
    status: ContractStatus = ContractStatus.DRAFT
    pillar: Pillar

    counterparty_organisation_id: str | None = None
    counterparty_person_id: str | None = Field(
        default=None,
        description="For the agreements whose counterparty is a person rather than a company: a "
        "consultant agreement, a founders service agreement.",
    )

    parent_contract_id: str | None = Field(
        default=None, description="The MSA a schedule belongs to."
    )
    dated_on: date | None = None
    effective_on: date | None = None
    signed_on: date | None = None
    governing_law: str | None = Field(
        default=None, description="e.g. 'State of New York' or 'Switzerland'."
    )
    terms: tuple[ContractTerm, ...] = ()
    documents: tuple[ContractDocument, ...] = ()

    @model_validator(mode="after")
    def _exactly_one_counterparty(self) -> Contract:
        org = self.counterparty_organisation_id
        person = self.counterparty_person_id
        if bool(org) == bool(person):
            raise ValueError(
                "a contract has exactly one counterparty: an organisation or a person, not both "
                "and not neither. A contract with nobody on the other side is not a contract."
            )
        return self

    @model_validator(mode="after")
    def _signed_contracts_have_a_signing_date(self) -> Contract:
        signed_states = {
            ContractStatus.SIGNED,
            ContractStatus.ACTIVE,
            ContractStatus.EXPIRED,
            ContractStatus.TERMINATED,
        }
        if self.status in signed_states and self.signed_on is None:
            raise ValueError(
                f"a contract in status {self.status.value!r} has been signed, so signed_on is "
                "required. Every commission window in this record is measured from a date, and a "
                "window with no start does not compute."
            )
        return self

    @model_validator(mode="after")
    def _a_schedule_is_not_its_own_parent(self) -> Contract:
        if self.parent_contract_id is not None and self.parent_contract_id == self.id:
            raise ValueError(f"contract {self.id!r} cannot be its own parent")
        return self
