"""The group-level record's shapes (HC-005).

Holy Corner owns this half of the contract surface. These tests hold up the invariants that are
expressed as validators rather than as conventions, because a rule the type does not enforce is a
rule somebody works around at three in the morning.

## Why the figures here are invented

HC-005 asks for a test built from the real commercial record. **The figures used below are
deliberately fictional**, and the structures are real.

This repository is public, and so is the hub's. Holy Corner's HC-056 exists to get Bruntsfield's
negotiated commission rates, commitment amounts and equity terms OUT of public repositories,
because both advisory agreements carry a Most-Favoured-Nation clause and those rates are not meant
to be common knowledge. Copying them into a test here would add another place to scrub and would
work directly against that ticket, for no gain: what these tests need to prove is that the SHAPES
can carry the real record, and a shape is proved by its structure, not by its values.

The assertion that the actual terms are representable belongs where the actual terms belong, which
after HC-056 is not a public repository.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from bcap_contracts.approvals import (
    Actor,
    ActorKind,
    ApprovalEvent,
    ApprovalEventType,
    Proposal,
    ProposalStatus,
)
from bcap_contracts.contracts import (
    CommissionRate,
    CommitmentPayment,
    Contract,
    ContractStatus,
    ContractType,
    EquitySplit,
    LongStop,
    Milestone,
)
from bcap_contracts.invoices import (
    Expense,
    ExpenseAllocation,
    Invoice,
    InvoiceLine,
    InvoiceStatus,
    Payment,
)
from bcap_contracts.money import Currency, Money, RecordedAmount
from bcap_contracts.organisations import (
    Organisation,
    OrganisationRelationship,
    OrganisationType,
    Person,
    PersonKind,
    Pillar,
    RelationshipKind,
)
from pydantic import ValidationError

NOW = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)


def usd(minor: int, ref: str = "test fixture") -> RecordedAmount:
    return RecordedAmount(amount_minor=minor, currency=Currency.USD, source_ref=ref)


# --------------------------------------------------------------------------- #
# RecordedAmount, and why it is not Money
# --------------------------------------------------------------------------- #
class TestRecordedAmount:
    def test_an_amount_cannot_exist_without_its_source(self) -> None:
        with pytest.raises(ValidationError):
            RecordedAmount(amount_minor=1, currency=Currency.USD, source_ref="   ")

    def test_it_is_a_different_type_from_money_and_does_not_convert(self) -> None:
        # Money carries the assumptions that justify a modelled figure; RecordedAmount carries the
        # source a fact was read from. Neither is constructible from the other, and this package
        # defines nothing that turns one into the other.
        modelled = Money(amount_minor=1, currency=Currency.USD, assumption_register_ref="AR-1")
        observed = usd(1, "INV-001")
        assert type(modelled) is not type(observed)
        assert not hasattr(observed, "assumption_register_ref")
        assert not hasattr(modelled, "source_ref")

    def test_it_is_frozen_so_an_amount_cannot_be_edited_after_the_fact(self) -> None:
        amount = usd(500)
        with pytest.raises(ValidationError):
            amount.amount_minor = 5_000_000  # type: ignore[misc]


# --------------------------------------------------------------------------- #
# The register
# --------------------------------------------------------------------------- #
class TestOrganisations:
    def test_one_organisation_can_belong_to_several_pillars(self) -> None:
        # An advisory partner today may be a briefing subject tomorrow. The register holds that
        # without duplicating the record once per pillar.
        org = Organisation(
            id="acme",
            canonical_name="Acme Data, Inc.",
            type=OrganisationType.PARTNER,
            countries=("US", "GB"),
            pillar_flags=(Pillar.ADVISORY, Pillar.BRIEFING),
        )
        assert set(org.pillar_flags) == {Pillar.ADVISORY, Pillar.BRIEFING}

    @pytest.mark.parametrize("bad", [("USA",), ("us",), ("U",), ("United States",)])
    def test_a_country_must_be_a_two_letter_code(self, bad: tuple[str, ...]) -> None:
        # A register that accepts three spellings of one country cannot group by it.
        with pytest.raises(ValidationError):
            Organisation(id="x", canonical_name="X", type=OrganisationType.OTHER, countries=bad)

    def test_an_organisation_cannot_relate_to_itself(self) -> None:
        with pytest.raises(ValidationError):
            OrganisationRelationship(
                source_organisation_id="acme",
                target_organisation_id="acme",
                kind=RelationshipKind.OWNS,
            )

    def test_a_person_holds_every_address_that_is_them(self) -> None:
        # The Managing Partner signs from one address and administrates under another, and "who is
        # this" must not depend on which one they used.
        person = Person(
            id="p1",
            name="A Person",
            kind=PersonKind.STAFF,
            emails=("a@example.com", "a.person@example.org"),
        )
        assert len(person.emails) == 2

    @pytest.mark.parametrize(
        "emails", [("A@Example.com",), ("a@example.com", "a@example.com"), ("not-an-email",)]
    )
    def test_addresses_are_lower_cased_unique_and_actually_addresses(
        self, emails: tuple[str, ...]
    ) -> None:
        with pytest.raises(ValidationError):
            Person(id="p", name="P", kind=PersonKind.STAFF, emails=emails)


# --------------------------------------------------------------------------- #
# Contracts and their terms
# --------------------------------------------------------------------------- #
class TestContracts:
    def test_an_advisory_shape_carries_rates_and_a_commitment_payment(self) -> None:
        # The SHAPE of an advisory engagement schedule: a per-year commission rate with a window,
        # and a payment on signature that may or may not be creditable. Figures invented.
        contract = Contract(
            id="acme-schedule-v1",
            type=ContractType.ENGAGEMENT_SCHEDULE,
            pillar=Pillar.ADVISORY,
            status=ContractStatus.ACTIVE,
            counterparty_organisation_id="acme",
            parent_contract_id="acme-msa-v1",
            dated_on=date(2026, 1, 5),
            effective_on=date(2026, 1, 1),
            signed_on=date(2026, 1, 6),
            governing_law="State of New York",
            terms=(
                CommissionRate(
                    engagement_type="referral", yr1_bps=1111, yr2_bps=777, window_months=18
                ),
                CommitmentPayment(amount=usd(123_456), creditable=True),
            ),
        )
        assert len(contract.terms) == 2
        assert contract.terms[0].kind == "commission_rate"
        assert contract.terms[1].kind == "commitment_payment"

    def test_a_foundry_shape_carries_a_milestone_an_equity_split_and_a_long_stop(self) -> None:
        # A venture earns nothing and is measured by whether it can support its founder. The same
        # Contract type holds it, with different terms, and no null columns anywhere.
        contract = Contract(
            id="venture-agreement-v1",
            type=ContractType.COLLABORATION_AGREEMENT,
            pillar=Pillar.FOUNDRY,
            status=ContractStatus.ACTIVE,
            counterparty_person_id="a-founder",
            signed_on=date(2026, 2, 2),
            terms=(
                Milestone(
                    description="can support the founder full time",
                    measure="net_revenue_per_month",
                    threshold=RecordedAmount(
                        amount_minor=111_100, currency=Currency.GBP, source_ref="term sheet"
                    ),
                    sustained_months=3,
                ),
                EquitySplit(
                    holder="founder", bps=4_444, vesting_months=36, cliff_months=6, provisional=True
                ),
                LongStop(months=18, remedy="the founder may require spin-out", provisional=True),
            ),
        )
        kinds = [t.kind for t in contract.terms]
        assert kinds == ["milestone", "equity_split", "long_stop"]

    def test_a_bracketed_figure_is_recorded_as_provisional(self) -> None:
        # A signed document carries some figures in square brackets. Recording a negotiating
        # position as though it were agreed is how it becomes a fact nobody remembers agreeing to.
        split = EquitySplit(holder="bruntsfield", bps=4_000, provisional=True)
        assert split.provisional is True

    def test_a_contract_has_exactly_one_counterparty(self) -> None:
        # A contract with nobody on the other side is not a contract, and one with two is a record
        # that cannot say who owes whom.
        with pytest.raises(ValidationError):
            Contract(
                id="x",
                type=ContractType.MSA,
                pillar=Pillar.ADVISORY,
                counterparty_organisation_id="a",
                counterparty_person_id="b",
            )
        with pytest.raises(ValidationError):
            Contract(id="x", type=ContractType.MSA, pillar=Pillar.ADVISORY)

    def test_a_signed_contract_must_say_when_it_was_signed(self) -> None:
        # Every commission window in this record is measured from a date. A window with no start
        # does not compute.
        with pytest.raises(ValidationError):
            Contract(
                id="x",
                type=ContractType.MSA,
                pillar=Pillar.ADVISORY,
                counterparty_organisation_id="a",
                status=ContractStatus.ACTIVE,
            )

    def test_two_disagreeing_dates_are_both_kept(self) -> None:
        # One real agreement has an MSA dated one day and a schedule saying it was entered into
        # five weeks earlier. Collapsing them loses a discrepancy somebody has to decide about.
        contract = Contract(
            id="x",
            type=ContractType.ENGAGEMENT_SCHEDULE,
            pillar=Pillar.ADVISORY,
            counterparty_organisation_id="a",
            dated_on=date(2026, 6, 5),
            effective_on=date(2026, 5, 8),
        )
        assert contract.dated_on != contract.effective_on

    def test_a_cliff_cannot_outlast_its_vesting(self) -> None:
        with pytest.raises(ValidationError):
            EquitySplit(holder="f", bps=5_000, vesting_months=12, cliff_months=48)

    def test_a_rate_is_basis_points_and_cannot_exceed_the_whole(self) -> None:
        with pytest.raises(ValidationError):
            CommissionRate(engagement_type="x", yr1_bps=10_001, yr2_bps=0, window_months=12)

    def test_terms_round_trip_through_json_with_their_kind_intact(self) -> None:
        # The discriminator is the reason a consumer does not have to guess which shape it got back.
        contract = Contract(
            id="x",
            type=ContractType.MSA,
            pillar=Pillar.ADVISORY,
            counterparty_organisation_id="a",
            terms=(
                CommissionRate(engagement_type="y", yr1_bps=100, yr2_bps=50, window_months=12),
                LongStop(months=24),
            ),
        )
        again = Contract.model_validate_json(contract.model_dump_json())
        assert [t.kind for t in again.terms] == ["commission_rate", "long_stop"]
        assert again == contract


# --------------------------------------------------------------------------- #
# Money out and money in
# --------------------------------------------------------------------------- #
class TestInvoices:
    def test_an_invoice_is_denominated_in_one_currency_throughout(self) -> None:
        with pytest.raises(ValidationError):
            Invoice(
                id="i",
                number="INV-9",
                issuer_organisation_id="us",
                billed_to_organisation_id="them",
                currency=Currency.USD,
                total=RecordedAmount(amount_minor=1, currency=Currency.GBP, source_ref="x"),
            )

    def test_a_line_in_another_currency_is_refused(self) -> None:
        with pytest.raises(ValidationError):
            Invoice(
                id="i",
                number="INV-9",
                issuer_organisation_id="us",
                billed_to_organisation_id="them",
                currency=Currency.USD,
                total=usd(100),
                lines=(
                    InvoiceLine(
                        description="x",
                        unit_amount=RecordedAmount(
                            amount_minor=100, currency=Currency.EUR, source_ref="x"
                        ),
                    ),
                ),
            )

    def test_an_issued_invoice_must_have_an_issue_date(self) -> None:
        # "Overdue" is derived from a date, so there has to be one to derive it from.
        with pytest.raises(ValidationError):
            Invoice(
                id="i",
                number="INV-9",
                issuer_organisation_id="us",
                billed_to_organisation_id="them",
                currency=Currency.USD,
                total=usd(100),
                status=InvoiceStatus.SENT,
            )

    def test_an_fx_rate_and_its_source_travel_together(self) -> None:
        # A rate with no source is a number somebody typed.
        with pytest.raises(ValidationError):
            Payment(id="p", received_on=date(2026, 9, 1), amount=usd(1), fx_rate="1.2700")

    def test_a_payment_cannot_be_matched_to_no_invoice(self) -> None:
        from bcap_contracts.invoices import MatchedBy

        with pytest.raises(ValidationError):
            Payment(
                id="p",
                received_on=date(2026, 9, 1),
                amount=usd(1),
                matched_by=MatchedBy.AUTO,
            )

    def test_a_confirmed_expense_has_somewhere_to_go(self) -> None:
        # Confirming an allocation to nowhere makes a cost vanish from every pillar at once.
        with pytest.raises(ValidationError):
            Expense(
                id="e",
                amount=usd(1),
                incurred_on=date(2026, 9, 1),
                allocation=ExpenseAllocation.CONFIRMED,
            )


# --------------------------------------------------------------------------- #
# The gate
# --------------------------------------------------------------------------- #
class TestApprovals:
    PROPOSER = Actor(kind=ActorKind.AGENT, id="composer")
    HUMAN = Actor(kind=ActorKind.HUMAN, id="a@b.c")

    @pytest.mark.parametrize("kind", [ActorKind.AGENT, ActorKind.EXECUTOR])
    @pytest.mark.parametrize("decision", [ApprovalEventType.GRANTED, ApprovalEventType.REJECTED])
    def test_only_a_human_may_grant_or_reject(
        self, kind: ActorKind, decision: ApprovalEventType
    ) -> None:
        # An agent that can grant its own proposal is the gate removed. A self-declared actor is
        # not authorisation.
        with pytest.raises(ValidationError):
            ApprovalEvent(
                seq=1,
                scope="invoice:INV-9",
                id="prop-1",
                type=decision,
                at=NOW,
                actor=Actor(kind=kind, id="x"),
                content_hash="abc",
            )

    @pytest.mark.parametrize(
        "doing",
        [
            ApprovalEventType.EXECUTING,
            ApprovalEventType.EXECUTED,
            ApprovalEventType.FAILED,
        ],
    )
    def test_only_the_executor_performs_an_external_action(self, doing: ApprovalEventType) -> None:
        with pytest.raises(ValidationError):
            ApprovalEvent(
                seq=1,
                scope="invoice:INV-9",
                id="prop-1",
                type=doing,
                at=NOW,
                actor=self.HUMAN,
            )

    def test_a_grant_must_name_what_it_approved(self) -> None:
        # Without the content hash there is nothing stopping the payload changing between the yes
        # and the doing, which is the difference between approving a payment and approving an
        # amount.
        with pytest.raises(ValidationError):
            ApprovalEvent(
                seq=2,
                scope="invoice:INV-9",
                id="prop-1",
                type=ApprovalEventType.GRANTED,
                at=NOW,
                actor=self.HUMAN,
            )

    def test_a_granted_event_with_its_hash_is_accepted(self) -> None:
        event = ApprovalEvent(
            seq=2,
            scope="invoice:INV-9",
            id="prop-1",
            type=ApprovalEventType.GRANTED,
            at=NOW,
            actor=self.HUMAN,
            content_hash="sha256:abc",
        )
        assert event.actor.kind is ActorKind.HUMAN

    def test_an_event_is_immutable_once_made(self) -> None:
        event = ApprovalEvent(
            seq=1,
            scope="s",
            id="prop-1",
            type=ApprovalEventType.PROPOSED,
            at=NOW,
            actor=self.PROPOSER,
        )
        with pytest.raises(ValidationError):
            event.seq = 99  # type: ignore[misc]

    def test_a_decided_proposal_names_who_decided_it(self) -> None:
        # A decision with nobody attached is the question this log exists to answer.
        with pytest.raises(ValidationError):
            Proposal(
                id="p",
                scope="s",
                kind="invoice.send",
                subject="INV-9",
                status=ProposalStatus.GRANTED,
                proposed_at=NOW,
                proposed_by=self.PROPOSER,
            )

    def test_refused_events_are_counted_and_shown(self) -> None:
        # A trail that quietly drops what it cannot read is worse than one with a visible hole.
        proposal = Proposal(
            id="p",
            scope="s",
            kind="invoice.send",
            subject="INV-9",
            status=ProposalStatus.PROPOSED,
            proposed_at=NOW,
            proposed_by=self.PROPOSER,
            refused_events=2,
        )
        assert proposal.refused_events == 2


# --------------------------------------------------------------------------- #
# Every new model refuses what it does not know about
# --------------------------------------------------------------------------- #
def test_every_new_model_forbids_extra_fields() -> None:
    # extra="forbid" everywhere: a typo in a field name must be an error, not a silently ignored
    # value that the writer believes was saved.
    Organisation(id="x", canonical_name="X", type=OrganisationType.OTHER)
    with pytest.raises(ValidationError):
        Organisation(
            id="x",
            canonical_name="X",
            type=OrganisationType.OTHER,
            definitely_not_a_field="oops",  # type: ignore[call-arg]
        )

    Person(id="x", name="X", kind=PersonKind.STAFF)
    with pytest.raises(ValidationError):
        Person(
            id="x",
            name="X",
            kind=PersonKind.STAFF,
            definitely_not_a_field="oops",  # type: ignore[call-arg]
        )

    Contract(
        id="x", type=ContractType.MSA, pillar=Pillar.ADVISORY, counterparty_organisation_id="a"
    )
    with pytest.raises(ValidationError):
        Contract(
            id="x",
            type=ContractType.MSA,
            pillar=Pillar.ADVISORY,
            counterparty_organisation_id="a",
            definitely_not_a_field="oops",  # type: ignore[call-arg]
        )

    Invoice(
        id="x",
        number="N",
        issuer_organisation_id="a",
        billed_to_organisation_id="b",
        currency=Currency.USD,
        total=usd(1),
    )
    with pytest.raises(ValidationError):
        Invoice(
            id="x",
            number="N",
            issuer_organisation_id="a",
            billed_to_organisation_id="b",
            currency=Currency.USD,
            total=usd(1),
            definitely_not_a_field="oops",  # type: ignore[call-arg]
        )
