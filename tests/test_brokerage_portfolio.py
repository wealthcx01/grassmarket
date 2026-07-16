"""GRS-0071 — the "Your Brokerages" portfolio view. It must be owner-scoped (CLAUDE.md #9), surface
each assessment's segment from its business profile, and carry no score until finalised."""

from __future__ import annotations

from bcap_contracts.assessments import AssessmentDocument, BusinessProfile
from fastapi.testclient import TestClient

from grassmarket.data.repository import Repository
from tests.conftest import SeededConsultant, auth_header


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


def test_portfolio_has_no_score_until_finalised(repo: Repository, alice: SeededConsultant) -> None:
    repo.create_assessment(alice.principal, subject="Draft Co")
    entry = repo.list_brokerage_portfolio(alice.principal)[0]
    assert entry.state == "draft"
    assert entry.v_index is None
    assert entry.uncertainty_rating is None


def test_portfolio_is_newest_touched_first(repo: Repository, alice: SeededConsultant) -> None:
    first = repo.create_assessment(alice.principal, subject="First")
    repo.create_assessment(alice.principal, subject="Second")
    # Touch the first so it becomes the most-recently-updated.
    repo.update_assessment(alice.principal, first.id, document=AssessmentDocument(subject="First"))
    subjects = [e.subject for e in repo.list_brokerage_portfolio(alice.principal)]
    assert subjects[0] == "First"


# --------------------------------------------------------------------- HTTP surface (CLAUDE.md #9)
def test_http_portfolio_route_resolves_and_is_scoped(
    client: TestClient, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    """`/assessments/portfolio` must resolve to the portfolio handler (not be parsed as
    `/{assessment_id}` — the 422 UUID trap), return the caller's own rows, and hide others'."""
    created = client.post("/assessments", json={"subject": "AliceCo"}, headers=auth_header(alice))
    assert created.status_code == 201

    resp = client.get("/assessments/portfolio", headers=auth_header(alice))
    assert resp.status_code == 200  # route resolved — not a 422 "value is not a valid uuid"
    assert [e["subject"] for e in resp.json()] == ["AliceCo"]

    # Bob sees an empty portfolio — never Alice's book.
    bob_resp = client.get("/assessments/portfolio", headers=auth_header(bob))
    assert bob_resp.status_code == 200
    assert bob_resp.json() == []


def test_http_portfolio_requires_authentication(client: TestClient) -> None:
    assert client.get("/assessments/portfolio").status_code == 401
