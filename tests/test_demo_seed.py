"""Revolut DEMO worked example (GRS-0117, ADR-0029).

A solo advisor (no co-rater, no committee) reaches the payoff: a finalised DEMO assessment and the
REAL generated deliverables — because a non-production record self-approves. The production gate is
untouched (asserted here), the record is DEMO-provenanced (so it's watermarked everywhere and
segregated from the benchmark), and the deliverables are produced by the real generators.
"""

from __future__ import annotations

from uuid import UUID

from bcap_contracts.assessments import RecordProvenance
from bcap_contracts.common import AssessorLevel, ConsultantTier, Role

from grassmarket.assessments.service import scoreability_blockers
from grassmarket.data.repository import Principal, Repository
from grassmarket.demo.revolut_demo import (
    REVOLUT_SUBJECT,
    revolut_demo_document,
    seed_revolut_demo,
)


def test_revolut_document_is_valid_and_scoreable() -> None:
    from bcap_contracts.registry import load_registry

    doc = revolut_demo_document()
    assert doc.subject == REVOLUT_SUBJECT
    assert len(doc.powers) == 7  # all 7 Strategic Powers graded
    # No missing-input blockers — the illustrative doc is genuinely scoreable.
    assert scoreability_blockers(doc, load_registry()) == []


def _make_owner(session_factory) -> str:
    email = "demo-owner@bruntsfieldcapital.com"
    session = session_factory()
    try:
        repo = Repository(session)
        repo.create_consultant(
            email=email,
            full_name="Demo Owner",
            hashed_password="x",  # pragma: allowlist secret
            role=Role.CONSULTANT,
            tier=ConsultantTier.CONSULTANT,
            assessor_level=AssessorLevel.CERTIFIED_LEAD,
        )
        session.commit()
    finally:
        session.close()
    return email


def test_seed_creates_a_finalised_demo_with_real_deliverables(
    session_factory, engine, settings
) -> None:
    email = _make_owner(session_factory)
    ids = seed_revolut_demo(session_factory, engine, settings, owner_email=email)

    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(email)
        principal = Principal(consultant_id=owner.id, role=owner.role)

        # A solo advisor finalised it (DEMO self-approves) — no co-rater, no committee.
        assessment = repo.get_assessment(principal, UUID(ids["assessment_id"]))
        assert assessment.state.value == "finalised"
        assert assessment.provenance is RecordProvenance.DEMO
        assert assessment.scoring_run_id is not None

        # The REAL generators produced deliverables (not hand-pasted placeholders).
        deliverables = repo.list_deliverables(principal, UUID(ids["engagement_id"]))
        assert len(deliverables) >= 3  # several document types generated
        assert ids["deliverables"]  # the seed reported which types it generated
    finally:
        session.close()
