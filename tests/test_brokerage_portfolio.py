"""GRS-0071 — the "Your Brokerages" portfolio view. It must be owner-scoped (CLAUDE.md #9), surface
each assessment's segment from its business profile, and carry no score until finalised."""

from __future__ import annotations

from bcap_contracts.assessments import AssessmentDocument, BusinessProfile

from grassmarket.data.repository import Repository
from tests.conftest import SeededConsultant


def test_portfolio_is_owner_scoped_and_surfaces_segment(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    a1 = repo.create_assessment(alice.principal, subject="Meridian")
    repo.update_assessment(
        alice.principal,
        a1.id,
        document=AssessmentDocument(
            subject="Meridian", profile=BusinessProfile(segment="Retail broker")
        ),
    )
    repo.create_assessment(alice.principal, subject="Northgate")
    repo.create_assessment(bob.principal, subject="Bob's Brokerage")

    alice_portfolio = repo.list_brokerage_portfolio(alice.principal)
    bob_portfolio = repo.list_brokerage_portfolio(bob.principal)

    assert {e.subject for e in alice_portfolio} == {"Meridian", "Northgate"}
    assert {e.subject for e in bob_portfolio} == {"Bob's Brokerage"}
    meridian = next(e for e in alice_portfolio if e.subject == "Meridian")
    assert meridian.segment == "Retail broker"
    # An assessment with no profile set surfaces a null segment, never a fabricated one.
    assert next(e for e in alice_portfolio if e.subject == "Northgate").segment is None


def test_portfolio_has_no_score_until_finalised(
    repo: Repository, alice: SeededConsultant
) -> None:
    repo.create_assessment(alice.principal, subject="Draft Co")
    entry = repo.list_brokerage_portfolio(alice.principal)[0]
    assert entry.state == "draft"
    assert entry.v_index is None
    assert entry.uncertainty_rating is None


def test_portfolio_is_newest_touched_first(
    repo: Repository, alice: SeededConsultant
) -> None:
    first = repo.create_assessment(alice.principal, subject="First")
    repo.create_assessment(alice.principal, subject="Second")
    # Touch the first so it becomes the most-recently-updated.
    repo.update_assessment(alice.principal, first.id, document=AssessmentDocument(subject="First"))
    subjects = [e.subject for e in repo.list_brokerage_portfolio(alice.principal)]
    assert subjects[0] == "First"
