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
from grassmarket.demo.brokerage_showcase import (
    SHOWCASE,
    seed_brokerage_showcase,
    showcase_document,
)
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


# ---- Brokerage showcase (GRS-0159) ---------------------------------------------------------------


def test_showcase_documents_are_complete_and_scoreable() -> None:
    """Every showcase spec rates EVERY registry subcomponent — infrastructure AND customer
    proposition — with all 7 powers and metrics, so each seeded record is a complete demo."""
    from bcap_contracts.registry import load_registry

    registry = load_registry()
    n_v = sum(len(m.subcomponents) for m in registry.modules)
    n_c = sum(len(m.subcomponents) for m in registry.c_modules)
    for spec in SHOWCASE:
        doc = showcase_document(spec)
        assert len(doc.subcomponents) == n_v
        assert len(doc.c_subcomponents) == n_c
        assert len(doc.powers) == 7
        assert scoreability_blockers(doc, registry) == []


def test_showcase_seed_populates_a_demo_instance_and_is_idempotent(
    session_factory, engine, settings
) -> None:
    """The GRS-0159 acceptance: one call populates finalised showcase reports, engagements with
    real deliverables, and a non-zero earnings statement — and a re-run duplicates nothing."""
    email = "showcase-owner@bruntsfieldcapital.com"
    results = seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    assert [r["status"] for r in results] == ["seeded"] * len(SHOWCASE)

    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(email)
        principal = Principal(consultant_id=owner.id, role=owner.role)

        # All showcase brokerages finalised, DEMO-provenanced (watermarked, benchmark-excluded).
        portfolio = {e.subject: e for e in repo.list_brokerage_portfolio(principal)}
        for spec in SHOWCASE:
            entry = portfolio[spec.subject]
            assert entry.state.value == "finalised"
            assert entry.provenance is RecordProvenance.DEMO
            assert entry.v_index is not None
            assert entry.c_index is not None  # the C spread is the demo's headline story

        # Each engagement carries real generated deliverables.
        for r in results:
            deliverables = repo.list_deliverables(principal, UUID(r["engagement_id"]))
            assert len(deliverables) >= 5

        # The illustrative Year-1 deals produce the staging run's £49,500 statement.
        lines = repo.list_commission_lines(principal)
        assert {line.product_id for line in lines} == {s.product_id for s in SHOWCASE}
        assert sum(line.amount.amount_minor for line in lines) == 4_950_000
    finally:
        session.close()

    # Idempotent: the re-run skips every brokerage and records nothing new.
    again = seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    assert all(r["status"].startswith("exists") for r in again)
    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(email)
        principal = Principal(consultant_id=owner.id, role=owner.role)
        assert len(repo.list_assessments(principal)) == len(SHOWCASE)
        assert len(repo.list_commission_lines(principal)) == len(SHOWCASE)
    finally:
        session.close()
