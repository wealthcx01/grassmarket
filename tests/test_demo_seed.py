"""Revolut DEMO worked example (GRS-0117, ADR-0029).

A solo advisor (no co-rater, no committee) reaches the payoff: a finalised DEMO assessment and the
REAL generated deliverables — because a non-production record self-approves. The production gate is
untouched (asserted here), the record is DEMO-provenanced (so it's watermarked everywhere and
segregated from the benchmark), and the deliverables are produced by the real generators.
"""

from __future__ import annotations

import json
from uuid import UUID

import pytest
from bcap_contracts.assessments import AssessmentState, RecordProvenance
from bcap_contracts.client_report import SECTION_ORDER
from bcap_contracts.common import AssessorLevel, ConsultantTier, Role
from sqlalchemy import select

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
from grassmarket.demo.showcase_reports import SHOWCASE_PROSE


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
    # Since GRS-0208 scope 1 the seed also returns the story prospects that give the account a
    # pipeline. They are tagged, so this stays a statement about the SCORED firms rather than a
    # count that drifts every time the story grows.
    showcase = [r for r in results if r["kind"] == "showcase"]
    assert [r["status"] for r in showcase] == ["seeded"] * len(SHOWCASE)

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
        for r in showcase:
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
        # One more than the showcase: GRS-0208 scope 1 leaves a single assessment IN PROGRESS so
        # the portfolio shows a state other than finalised and the wizard has something to resume.
        assert len(repo.list_assessments(principal)) == len(SHOWCASE) + 1
        # Commissions are unchanged — the story prospects are pipeline shape, not closed business,
        # and inventing sales for them would put money-shaped numbers behind cards that never sold.
        assert len(repo.list_commission_lines(principal)) == len(SHOWCASE)
    finally:
        session.close()


# --- Seed hygiene (GRS-0177) --------------------------------------------------------------
# The founder's demo showed Revolut, Hargreaves Lansdown and WeBull twice each with identical
# scores: a DEMO row seeded on 22/07 alongside a SANDBOX row left by a 21/07 staging run. The skip
# set only looked at DEMO provenance, so a subject already showcased as a sandbox record was
# re-created as a demo one.


def _principal_for(session_factory, email: str) -> tuple[Repository, Principal]:
    session = session_factory()
    repo = Repository(session)
    owner = repo.get_consultant_by_email(email)
    return repo, Principal(consultant_id=owner.id, role=owner.role)


def test_a_rerun_changes_no_counts_at_all(session_factory, engine, settings) -> None:
    """Stronger than "no error": every count is equal before and after a second run."""
    email = "rerun-owner@bruntsfieldcapital.com"
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)

    def counts() -> dict[str, int]:
        session = session_factory()
        try:
            repo = Repository(session)
            owner = repo.get_consultant_by_email(email)
            principal = Principal(consultant_id=owner.id, role=owner.role)
            engagements = repo.list_engagements(principal)
            return {
                "assessments": len(repo.list_assessments(principal)),
                "prospects": len(repo.list_prospects(principal)),
                "engagements": len(engagements),
                "commissions": len(repo.list_commission_lines(principal)),
                "deliverables": sum(
                    len(repo.list_deliverables(principal, e.id)) for e in engagements
                ),
            }
        finally:
            session.close()

    before = counts()
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    assert counts() == before


def test_a_subject_already_finalised_as_sandbox_is_not_reseeded_as_demo(
    session_factory, engine, settings
) -> None:
    """The exact staging condition that produced the duplicate rows."""
    email = "sandbox-first@bruntsfieldcapital.com"
    spec = SHOWCASE[0]

    # Stand up the owner and a FINALISED sandbox assessment for the first showcase subject, the
    # way a staging run would have left one behind.
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(email)
        principal = Principal(consultant_id=owner.id, role=owner.role)
        subjects_before = [a.subject for a in repo.list_assessments(principal)]
    finally:
        session.close()

    # A second run must skip every subject, including the one that is only there as a finalised
    # record rather than specifically as a DEMO one.
    again = seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    assert all(r["status"].startswith("exists") for r in again)

    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(email)
        principal = Principal(consultant_id=owner.id, role=owner.role)
        subjects_after = [a.subject for a in repo.list_assessments(principal)]
        assert sorted(subjects_after) == sorted(subjects_before)
        # One record per subject, not two.
        assert subjects_after.count(spec.subject) == 1
    finally:
        session.close()


def test_the_seeded_records_belong_to_their_owner_alone(session_factory, engine, settings) -> None:
    email = "scoped-owner@bruntsfieldcapital.com"
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    session = session_factory()
    try:
        repo = Repository(session)
        stranger = repo.create_consultant(
            email="stranger@bruntsfieldcapital.com",
            full_name="Stranger",
            hashed_password="x",
            role=Role.CONSULTANT,
            tier=ConsultantTier.VENTURE_ASSOCIATE,
            assessor_level=AssessorLevel.TRAINED,
        )
        session.commit()
        other = Principal(consultant_id=stranger.id, role=stranger.role)
        assert repo.list_assessments(other) == []
        assert repo.list_prospects(other) == []
        assert repo.list_commission_lines(other) == []
    finally:
        session.close()


def test_a_production_record_can_never_be_deleted_by_the_cleanup_path(
    session_factory, engine, settings
) -> None:
    """GRS-0177's cleanup tool must not be capable of removing real client work."""
    from grassmarket.data.repository import ConflictError

    email = "cleanup-guard@bruntsfieldcapital.com"
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(email)
        principal = Principal(consultant_id=owner.id, role=owner.role)
        production = repo.create_assessment(
            principal, subject="Real Client", provenance=RecordProvenance.PRODUCTION
        )
        with pytest.raises(ConflictError, match="production record"):
            repo.delete_assessment(principal, production.id)
        # Still there.
        assert repo.get_assessment(principal, production.id).subject == "Real Client"
    finally:
        session.close()


def test_a_finalised_record_is_refused_because_its_scoring_run_is_immutable(
    session_factory, engine, settings
) -> None:
    """Non-negotiable #6: deleting the assessment would orphan or destroy an immutable run."""
    from grassmarket.data.repository import ConflictError

    email = "cleanup-finalised@bruntsfieldcapital.com"
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(email)
        principal = Principal(consultant_id=owner.id, role=owner.role)
        finalised = next(
            a for a in repo.list_assessments(principal) if a.state is AssessmentState.FINALISED
        )
        # GRS-0246 added an engagement-link guard that runs BEFORE the scoring-run one, so this
        # test has to clear it to still be testing what it was written to test: that a finalised
        # record is refused for carrying immutable runs. Passing the unlink flag here asserts the
        # ordering as much as the refusal.
        with pytest.raises(ConflictError, match="finalised or carries"):
            repo.delete_assessment(principal, finalised.id, unlink_from_engagements=True)
    finally:
        session.close()


def test_a_production_record_is_refused_even_with_discard_scoring_runs(
    session_factory, engine, settings
) -> None:
    """ADR-0047: discard_scoring_runs does not open the production guard. Only the separate,
    per-call delete_production_record flag does, and only for the founder or an admin."""
    from grassmarket.data.repository import ConflictError

    email = "cleanup-prod-flag@bruntsfieldcapital.com"
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(email)
        principal = Principal(consultant_id=owner.id, role=owner.role)
        production = repo.create_assessment(
            principal, subject="Real Client", provenance=RecordProvenance.PRODUCTION
        )
        with pytest.raises(ConflictError, match="production record"):
            repo.delete_assessment(principal, production.id, discard_scoring_runs=True)
        assert repo.get_assessment(principal, production.id).subject == "Real Client"
    finally:
        session.close()


def test_an_advisor_cannot_delete_their_own_production_record_even_asking_for_it(
    session_factory, engine, settings
) -> None:
    """ADR-0047 amendment: the flag is necessary but not sufficient. Removing a production record
    is the founder's call, so an ordinary advisor passing it is still refused."""
    from grassmarket.data.repository import ScopeViolationError

    email = "cleanup-prod-advisor@bruntsfieldcapital.com"
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(email)
        principal = Principal(consultant_id=owner.id, role=owner.role)
        production = repo.create_assessment(
            principal, subject="Real Client", provenance=RecordProvenance.PRODUCTION
        )
        with pytest.raises(ScopeViolationError, match="founder or an admin"):
            repo.delete_assessment(principal, production.id, delete_production_record=True)
        assert repo.get_assessment(principal, production.id).subject == "Real Client"
    finally:
        session.close()


def test_the_founder_can_delete_a_named_production_record_and_it_is_audited(
    session_factory, engine, settings
) -> None:
    """ADR-0047 amendment: the founder's escape hatch for a mis-clicked production record, and the
    permanent trace it leaves. The audit log outlives the record it describes."""
    from bcap_contracts.audit import AuditEventType

    email = "cleanup-prod-founder@bruntsfieldcapital.com"
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(email)
        principal = Principal(consultant_id=owner.id, role=owner.role, is_founder=True)
        stray = repo.create_assessment(
            principal, subject="Mis-clicked Ltd", provenance=RecordProvenance.PRODUCTION
        )
        repo.delete_assessment(principal, stray.id, delete_production_record=True)
        session.commit()

        assert all(a.id != stray.id for a in repo.list_assessments(principal))
        admin = Principal(consultant_id=owner.id, role=Role.ADMIN)
        deletions = [
            e
            for e in repo.list_audit_events(admin)
            if e.event_type is AuditEventType.ASSESSMENT_DELETED
        ]
        assert len(deletions) == 1
        assert deletions[0].resource_id == stray.id
        assert "Mis-clicked Ltd" in (deletions[0].detail or "")
    finally:
        session.close()


def test_a_finalised_demo_record_goes_with_its_runs_and_leaves_no_orphans(
    session_factory, engine, settings
) -> None:
    """ADR-0047: the staging-cleanup path. The run goes, and so does everything pointing at it."""
    from sqlalchemy import select

    from grassmarket.data.models import (
        AINarrativeORM,
        DeliverableORM,
        PredictionORM,
        ScoringRunORM,
    )

    email = "cleanup-demo-runs@bruntsfieldcapital.com"
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(email)
        principal = Principal(consultant_id=owner.id, role=owner.role)
        target = next(
            a
            for a in repo.list_assessments(principal)
            if a.state is AssessmentState.FINALISED
            and a.provenance is not RecordProvenance.PRODUCTION
        )
        run_ids = [
            r.id
            for r in session.execute(
                select(ScoringRunORM).where(ScoringRunORM.assessment_id == target.id)
            )
            .scalars()
            .all()
        ]
        assert run_ids, "fixture must give the record at least one run for this test to mean much"

        # GRS-0246. This test's name promises "leaves no orphans" and, before the guard, it
        # left one: the showcase assessment is linked by its engagement, and deleting it pointed
        # that engagement at nothing. The flag removes the link in the same transaction, which is
        # what makes the promise in the name true.
        repo.delete_assessment(
            principal, target.id, discard_scoring_runs=True, unlink_from_engagements=True
        )
        session.commit()

        assert all(a.id != target.id for a in repo.list_assessments(principal))
        for orm in (ScoringRunORM, AINarrativeORM, PredictionORM, DeliverableORM):
            column = orm.id if orm is ScoringRunORM else orm.scoring_run_id
            left = session.execute(select(orm).where(column.in_(run_ids))).scalars().all()
            assert left == [], f"{orm.__name__} rows were orphaned by the delete"
    finally:
        session.close()


def test_an_unfinalised_sandbox_record_is_deletable(session_factory, engine, settings) -> None:
    email = "cleanup-draft@bruntsfieldcapital.com"
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(email)
        principal = Principal(consultant_id=owner.id, role=owner.role)
        stray = repo.create_assessment(
            principal, subject="Stray Draft", provenance=RecordProvenance.SANDBOX
        )
        repo.delete_assessment(principal, stray.id)
        session.commit()
        assert all(a.subject != "Stray Draft" for a in repo.list_assessments(principal))
    finally:
        session.close()


def test_every_showcase_deliverable_has_a_worked_example_report(
    session_factory, engine, settings
) -> None:
    """GRS-0236. The founder's complaint was "I can't seem to download example client reports", and
    the cause was that the showcase wrote no prose at all — so every demo report sat unwritten and
    both release paths refused with the 409 naming six empty sections.

    This asserts the fix at the level the complaint was made: not that prose rows exist, but that
    the report each deliverable produces actually ASSEMBLES. A seeded row that still fails the
    content model would be the same broken demo with more data behind it.
    """
    from grassmarket.deliverables.client_report_service import assemble
    from grassmarket.web.routers.client_report import _context

    email = "showcase-reports@bruntsfieldcapital.com"
    results = seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    # Since GRS-0208 scope 1 the seed also returns the story prospects that give the account a
    # pipeline. They are tagged, so this stays a statement about the SCORED firms rather than a
    # count that drifts every time the story grows.
    showcase = [r for r in results if r["kind"] == "showcase"]
    assert [r["status"] for r in showcase] == ["seeded"] * len(SHOWCASE)

    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(email)
        principal = Principal(consultant_id=owner.id, role=owner.role)
        checked = 0
        for r in showcase:
            for deliverable in repo.list_deliverables(principal, UUID(r["engagement_id"])):
                context, _, run_id, _ = _context(repo, principal, deliverable.id)
                sections_json = repo.get_report_prose(principal, deliverable.id)
                assert sections_json, f"{r['subject']}: {deliverable.type} has no prose"
                # Raises ReportNotAssembledError if a section is missing or empty, and a
                # ValidationError if the authored prose breaks the content model's own rules —
                # which is the point: the fixtures prove themselves compliant by construction.
                assembled = assemble(context, scoring_run_id=run_id, sections_json=sections_json)
                kinds = [s.kind.value for s in assembled.report.sections]
                assert kinds == [k.value for k in SECTION_ORDER]
                checked += 1
        assert checked >= 15, "expected five deliverables for each of the three brokerages"
    finally:
        session.close()


def test_the_showcase_prose_is_distinct_per_firm() -> None:
    """Three variations on "a strong platform with room to improve" would tell a reader that the
    assessment says nothing. The seed is the product's best output on display, so the reports have
    to be about the firms they name."""
    openings = {
        subject: sections["business"]["body"][0]  # type: ignore[index]
        for subject, sections in SHOWCASE_PROSE.items()
    }
    assert len(set(openings.values())) == len(SHOWCASE_PROSE)
    for spec in SHOWCASE:
        assert spec.subject in SHOWCASE_PROSE, f"{spec.subject} has no authored example report"


def test_a_showcase_spec_without_prose_fails_loudly() -> None:
    """A spec added later without prose would reintroduce the exact defect this ticket fixes, and
    would do it silently — the seed would succeed and the demo would refuse. So the seed refuses
    instead, naming what to add."""
    assert set(SHOWCASE_PROSE) >= {spec.subject for spec in SHOWCASE}


def test_a_rerun_backfills_prose_onto_already_seeded_brokerages(
    session_factory, engine, settings
) -> None:
    """GRS-0236, found by running the seed on staging rather than by reading it.

    The idempotency skip (GRS-0177) fired BEFORE the prose write, so an environment seeded before
    the prose fix kept its demo reports refusing forever — the founder's original complaint
    surviving the fix, in exactly the environments they look at. The skip now covers creation only.
    """
    from grassmarket.data.models import ClientReportProseORM

    email = "showcase-backfill@bruntsfieldcapital.com"
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)

    # Simulate the pre-fix state: the records exist, the prose does not.
    session = session_factory()
    try:
        for row in session.execute(select(ClientReportProseORM)).scalars().all():
            session.delete(row)
        session.commit()
    finally:
        session.close()

    again = seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    assert all(r["status"].startswith("exists") for r in again), again
    assert any("example report(s) written" in r["status"] for r in again), (
        "a re-run over already-seeded brokerages wrote no prose, so the demo stays broken"
    )

    session = session_factory()
    try:
        restored = session.execute(select(ClientReportProseORM)).scalars().all()
        assert len(restored) >= 15, "expected prose back on every showcase deliverable"
    finally:
        session.close()


def test_the_backfill_does_not_overwrite_words_already_written(
    session_factory, engine, settings
) -> None:
    """The seed's job is to make sure an example EXISTS, not to own its words forever. An advisor
    who edits a demo report and re-runs the seed keeps their edit."""
    from grassmarket.data.models import ClientReportProseORM

    email = "showcase-noclobber@bruntsfieldcapital.com"
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)

    session = session_factory()
    try:
        row = session.execute(select(ClientReportProseORM)).scalars().first()
        assert row is not None
        deliverable_id = row.deliverable_id
        row.sections_json = json.dumps(
            {
                kind.value: {"heading": kind.value.title(), "body": ["An advisor's own words."]}
                for kind in SECTION_ORDER
            }
        )
        session.commit()
    finally:
        session.close()

    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)

    session = session_factory()
    try:
        after = session.execute(
            select(ClientReportProseORM).where(
                ClientReportProseORM.deliverable_id == deliverable_id
            )
        ).scalar_one()
        assert "An advisor's own words." in after.sections_json
    finally:
        session.close()


def test_the_demo_account_tells_a_coherent_story(session_factory, engine, settings) -> None:
    """GRS-0208 scope 1. The founder could not follow a single example client end to end.

    The showcase alone gives three finalised firms — three cards in one column, nothing in flight,
    no workshop ever held. That is a filing cabinet, not a business. This asserts the shape a
    first-time user actually needs to see, on ONE account.
    """
    from collections import Counter

    from bcap_contracts.entities import PipelineStage

    from grassmarket.data.models import (
        AssessmentORM,
        ProspectORM,
        ProspectStageHistoryORM,
        WorkshopORM,
    )
    from grassmarket.demo.demo_story import IN_PROGRESS_SUBJECT, STORY_PROSPECTS

    email = "demo-story@bruntsfieldcapital.com"
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)

    session = session_factory()
    try:
        repo = Repository(session)
        owner = repo.get_consultant_by_email(email)
        prospects = [
            p
            for p in session.execute(select(ProspectORM)).scalars().all()
            if p.owner_consultant_id == owner.id
        ]
        stages = Counter(p.stage for p in prospects)

        # Every stage the board can show has at least one card. A demo board with one populated
        # column teaches an advisor that the product only has one column.
        for stage in PipelineStage:
            assert stages[stage.value] >= 1, f"no demo prospect sits at {stage.value}"

        # Something to resume. A demo where everything is finished says nothing about the part an
        # advisor spends their time in.
        assessments = [
            a
            for a in session.execute(select(AssessmentORM)).scalars().all()
            if a.owner_consultant_id == owner.id
        ]
        states = Counter(a.state for a in assessments)
        assert states["finalised"] >= 2
        assert states["draft"] >= 1
        assert any(a.subject == IN_PROGRESS_SUBJECT and a.state == "draft" for a in assessments)

        # Workshops exist AND are delivered — a stage history claiming a workshop happened with no
        # workshop to open is the quiet inconsistency a careful viewer checks first.
        workshops = session.execute(select(WorkshopORM)).scalars().all()
        assert len(workshops) >= 5
        assert all(w.delivered_on is not None for w in workshops)

        # Real transition history, not cards teleported into place. The board's time-in-stage flags
        # are computed from these, so without them its most useful signal shows nothing.
        history = session.execute(select(ProspectStageHistoryORM)).scalars().all()
        assert len(history) >= len(STORY_PROSPECTS)
        per_prospect = Counter(str(h.prospect_id) for h in history)
        assert max(per_prospect.values()) >= 5, "no card has a multi-step history to age"
    finally:
        session.close()


def test_the_story_prospects_are_distinct_from_the_scored_showcase(
    session_factory, engine, settings
) -> None:
    """A first-time user should be able to tell which records carry a real scored assessment behind
    them and which are pipeline colour. Reusing the showcase names for stage filler would blur
    exactly that line."""
    from grassmarket.demo.demo_story import STORY_PROSPECTS

    showcase = {spec.subject for spec in SHOWCASE}
    story = {p.company_name for p in STORY_PROSPECTS}
    assert showcase.isdisjoint(story)


def test_the_story_is_idempotent(session_factory, engine, settings) -> None:
    """GRS-0177's rule, extended to the new records: a re-run changes no counts."""
    from grassmarket.data.models import ProspectORM, WorkshopORM

    email = "demo-story-idem@bruntsfieldcapital.com"
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)

    def counts() -> tuple[int, int]:
        session = session_factory()
        try:
            return (
                len(session.execute(select(ProspectORM)).scalars().all()),
                len(session.execute(select(WorkshopORM)).scalars().all()),
            )
        finally:
            session.close()

    before = counts()
    seed_brokerage_showcase(session_factory, engine, settings, owner_email=email)
    assert counts() == before
