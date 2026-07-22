"""GRS-0071 — the "Your Brokerages" portfolio view. It must be owner-scoped (CLAUDE.md #9), surface
each assessment's segment from its business profile, and carry no score until finalised."""

from __future__ import annotations

from bcap_contracts.assessments import AssessmentDocument, BusinessProfile, SubcomponentRating
from bcap_contracts.common import EvidenceGrade, MaturityLevel, NonScoreState
from bcap_contracts.registry import load_registry
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
    assert meridian.segment == "Retail broker"  # explicit free-text segment wins
    # No free-text segment falls back to the operating-model NAME (retail is the scoring default),
    # so the column is never a bare "—" for an assessment that has an operating model (GRS-0163).
    northgate = next(e for e in alice_portfolio if e.subject == "Northgate")
    assert northgate.segment == "Retail brokerage"


def test_portfolio_has_no_score_until_finalised(repo: Repository, alice: SeededConsultant) -> None:
    repo.create_assessment(alice.principal, subject="Draft Co")
    entry = repo.list_brokerage_portfolio(alice.principal)[0]
    assert entry.state == "draft"
    assert entry.v_index is None
    assert entry.v_p10 is None
    assert entry.v_p90 is None
    assert entry.uncertainty_rating is None


def test_finalised_entry_carries_the_stored_band(
    client: TestClient, alice: SeededConsultant
) -> None:
    """GRS-0166: the portfolio row carries the run's stored P10/P90 alongside v_index, so the
    finalised wizard rail can quote the SAME locked score+band as this row and the deliverable —
    never a fresh Monte-Carlo recompute."""
    from grassmarket.demo.brokerage_showcase import REVOLUT, showcase_document

    headers = auth_header(alice)
    aid = client.post(
        "/assessments", json={"subject": "Revolut", "provenance": "sandbox"}, headers=headers
    ).json()["id"]
    doc = showcase_document(REVOLUT)
    assert (
        client.put(
            f"/assessments/{aid}", json=doc.model_dump(mode="json"), headers=headers
        ).status_code
        == 200
    )
    assert client.post(f"/assessments/{aid}/finalise", headers=headers).status_code == 200

    entry = client.get("/assessments/portfolio", headers=headers).json()[0]
    assert entry["v_index"] is not None
    assert entry["v_p10"] is not None and entry["v_p90"] is not None
    assert entry["v_p10"] <= entry["v_p90"]  # a band, stored at finalisation, not recomputed


def test_portfolio_surfaces_coverage(repo: Repository, alice: SeededConsultant) -> None:
    # Coverage = assessed / applicable (Not Applicable excluded), so a linked assessment's progress
    # reads at a glance (GRS-0116). Rate one subcomponent and mark one Not Applicable.
    registry = load_registry()
    total = len(registry.all_subcomponent_keys())
    module = registry.modules[0]
    a = repo.create_assessment(alice.principal, subject="Partly Assessed Co")
    repo.update_assessment(
        alice.principal,
        a.id,
        document=AssessmentDocument(
            subcomponents=(
                SubcomponentRating(
                    module_key=module.key,
                    subcomponent_key=module.subcomponents[0].key,
                    level=MaturityLevel.ADVANCED,
                    evidence_grade=EvidenceGrade.E3_ARTIFACT,
                ),
                SubcomponentRating(
                    module_key=module.key,
                    subcomponent_key=module.subcomponents[1].key,
                    state=NonScoreState.NOT_APPLICABLE,
                ),
            )
        ),
    )
    entry = next(
        e for e in repo.list_brokerage_portfolio(alice.principal) if e.assessment_id == a.id
    )
    # 1 assessed of (total − 1 Not Applicable) applicable.
    assert entry.coverage == round(1 / (total - 1), 4)

    # A brand-new assessment with nothing rated has 0 coverage (0 assessed / all applicable) —
    # never None unless nothing is applicable.
    fresh = repo.create_assessment(alice.principal, subject="Fresh Co")
    fresh_entry = next(
        e for e in repo.list_brokerage_portfolio(alice.principal) if e.assessment_id == fresh.id
    )
    assert fresh_entry.coverage == 0.0


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


def test_portfolio_surfaces_customer_proposition_index(
    repo: Repository, alice: SeededConsultant
) -> None:
    """C is reported alongside V (ADR-0023): document-derived and deterministic, so it surfaces on
    the portfolio row even for a draft — the demo-critical customer-experience score (GRS-0164)."""
    registry = load_registry()
    c_subs = tuple(
        SubcomponentRating(
            module_key=m.key,
            subcomponent_key=s.key,
            level=MaturityLevel.ADVANCED,
            evidence_grade=EvidenceGrade.E3_ARTIFACT,
        )
        for m in registry.c_modules
        for s in m.subcomponents
    )
    a = repo.create_assessment(alice.principal, subject="Customer Co")
    repo.update_assessment(
        alice.principal,
        a.id,
        document=AssessmentDocument(subject="Customer Co", c_subcomponents=c_subs),
    )
    entry = next(
        e for e in repo.list_brokerage_portfolio(alice.principal) if e.assessment_id == a.id
    )
    assert entry.c_index is not None
    assert 0.0 < entry.c_index <= 1.0


def test_portfolio_c_index_is_none_without_customer_data(
    repo: Repository, alice: SeededConsultant
) -> None:
    """No C inputs ⇒ C not scoreable ⇒ null, never a fabricated 0 (fail-loud honesty)."""
    a = repo.create_assessment(alice.principal, subject="No Customer Data Co")
    entry = next(
        e for e in repo.list_brokerage_portfolio(alice.principal) if e.assessment_id == a.id
    )
    assert entry.c_index is None
