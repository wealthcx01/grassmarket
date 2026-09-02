"""Deleting an assessment must not orphan an engagement (GRS-0246).

`delete_assessment` cascades carefully to everything referencing an assessment **by foreign key**.
An engagement used to reference its assessments through `assessment_ids_json`, a JSON text column —
no key, no cascade, nothing to notice. Five staging engagements pointed at deleted assessments for a
month because of it, and that is what made the founder's duplicate rows undeletable: they defaulted
to `production` because nothing could be derived from an assessment that no longer existed.

ADR-0047 §4 already said orphaned references are the silent inconsistency #3 exists to prevent. The
guarantee just never reached the one relationship not expressed as a key.

**GRS-0246 scope 1 closed that.** The links are rows in `engagement_assessments` with a real foreign
key, so the application guard below is now backed by the database: a link naming no assessment
cannot be written at all. `TestTheKeyMakesItImpossible` is the test that matters most here — the
rest guard the behaviour around it.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from bcap_contracts.assessments import RecordProvenance
from bcap_contracts.entities import PipelineStage
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from grassmarket.data.models import AssessmentORM, EngagementAssessmentORM
from grassmarket.data.repository import ConflictError, Repository

_TO_CONTRACTED = (
    PipelineStage.WORKSHOP_SCHEDULED,
    PipelineStage.WORKSHOP_DELIVERED,
    PipelineStage.QUALIFIED,
    PipelineStage.SCOPED,
    PipelineStage.CONTRACTED,
)


def _linked(repo: Repository, owner, company: str = "Acme"):
    """A demo assessment and an engagement that links it."""
    assessment = repo.create_assessment(
        owner.principal, subject=company, provenance=RecordProvenance.DEMO
    )
    row = repo._session.get(AssessmentORM, assessment.id)
    assert row is not None
    row.subject = company
    repo._session.flush()

    prospect = repo.create_prospect(owner.principal, company_name=company)
    for stage in _TO_CONTRACTED:
        prospect = repo.update_prospect_stage(owner.principal, prospect.id, stage)
    engagement = repo.create_engagement(
        owner.principal, prospect_id=prospect.id, title=f"{company} — delivery"
    )
    # Linked directly: `link_assessment_to_engagement` requires a finalised assessment, and this
    # test is about the deletion guard rather than the linking rules.
    repo._session.add(
        EngagementAssessmentORM(engagement_id=engagement.id, assessment_id=assessment.id)
    )
    repo._session.flush()
    return assessment, engagement


class TestTheKeyMakesItImpossible:
    """Scope 1: the class of bug is now structurally impossible, not merely detected."""

    def test_a_link_to_a_nonexistent_assessment_is_refused_by_the_database(
        self, repo: Repository, alice
    ) -> None:
        prospect = repo.create_prospect(alice.principal, company_name="Ghost")
        for stage in _TO_CONTRACTED:
            prospect = repo.update_prospect_stage(alice.principal, prospect.id, stage)
        engagement = repo.create_engagement(
            alice.principal, prospect_id=prospect.id, title="Ghost — delivery"
        )
        repo._session.add(
            EngagementAssessmentORM(engagement_id=engagement.id, assessment_id=uuid4())
        )
        with pytest.raises(IntegrityError):
            repo._session.flush()
        repo._session.rollback()

    def test_deleting_a_linked_assessment_is_refused_by_the_database_too(
        self, repo: Repository, alice
    ) -> None:
        """Belt and braces: even bypassing the repository guard, the key holds."""
        assessment, _ = _linked(repo, alice, "Monzo")
        repo._session.flush()
        # A typed delete, not raw SQL with a stringified UUID: SQLAlchemy stores Uuid as 32 hex
        # characters, so `WHERE id = '<dashed-uuid>'` matches no row and deletes nothing quietly.
        with pytest.raises(IntegrityError):
            repo._session.execute(delete(AssessmentORM).where(AssessmentORM.id == assessment.id))
            repo._session.flush()
        repo._session.rollback()


class TestTheGuard:
    def test_deleting_a_linked_assessment_is_refused(self, repo: Repository, alice) -> None:
        assessment, _ = _linked(repo, alice)
        with pytest.raises(ConflictError):
            repo.delete_assessment(alice.principal, assessment.id, discard_scoring_runs=True)

    def test_the_refusal_names_the_engagement(self, repo: Repository, alice) -> None:
        """A refusal that does not say what is in the way cannot be acted on."""
        assessment, _ = _linked(repo, alice, "WeBull")
        with pytest.raises(ConflictError) as exc:
            repo.delete_assessment(alice.principal, assessment.id, discard_scoring_runs=True)
        assert "WeBull — delivery" in str(exc.value)

    def test_an_unlinked_assessment_still_deletes(self, repo: Repository, alice) -> None:
        """The guard must not become a blanket refusal."""
        assessment = repo.create_assessment(
            alice.principal, subject="Solo", provenance=RecordProvenance.DEMO
        )
        repo.delete_assessment(alice.principal, assessment.id, discard_scoring_runs=True)
        assert repo._session.get(AssessmentORM, assessment.id) is None

    def test_another_advisors_engagement_still_blocks(self, repo: Repository, alice, bob) -> None:
        """Not owner-scoped, deliberately.

        The question is referential — would deleting this break something? — and an engagement
        belonging to someone else is exactly the one whose breakage nobody would notice.
        """
        assessment = repo.create_assessment(
            alice.principal, subject="Shared", provenance=RecordProvenance.DEMO
        )
        prospect = repo.create_prospect(bob.principal, company_name="Bobco")
        for stage in _TO_CONTRACTED:
            prospect = repo.update_prospect_stage(bob.principal, prospect.id, stage)
        theirs = repo.create_engagement(
            bob.principal, prospect_id=prospect.id, title="Bobco — delivery"
        )
        repo._session.add(
            EngagementAssessmentORM(engagement_id=theirs.id, assessment_id=assessment.id)
        )
        repo._session.flush()

        with pytest.raises(ConflictError):
            repo.delete_assessment(alice.principal, assessment.id, discard_scoring_runs=True)

    def test_an_unrelated_assessment_is_not_a_link(self, repo: Repository, alice) -> None:
        """An engagement that links nothing does not block an unrelated deletion.

        This replaces a test that stored a truncated UUID to prove the old JSON scan parsed rather
        than substring-matched. That failure mode no longer exists: a partial id is not a valid
        foreign key, so it cannot be written."""
        assessment = repo.create_assessment(
            alice.principal, subject="Solo", provenance=RecordProvenance.DEMO
        )
        prospect = repo.create_prospect(alice.principal, company_name="Other")
        for stage in _TO_CONTRACTED:
            prospect = repo.update_prospect_stage(alice.principal, prospect.id, stage)
        repo.create_engagement(alice.principal, prospect_id=prospect.id, title="Other — delivery")
        repo.delete_assessment(alice.principal, assessment.id, discard_scoring_runs=True)


class TestTheStandingCheck:
    """The check is kept for data that predates migration 0043, and as a cheap invariant.

    It can no longer be made to fire by any application path, and fabricating the state it looks
    for would mean disabling the foreign key — so the tests that used to do that have moved to
    `tests/test_migration.py`, where a database is migrated from 0042 with a dangling JSON entry
    and the entry is asserted to be dropped and reported. That is the only place the state can
    still legitimately arise.
    """

    def test_a_clean_database_reports_nothing(self, repo: Repository, alice) -> None:
        _linked(repo, alice)
        assert repo.dangling_assessment_references() == []

    def test_it_stays_empty_because_the_key_will_not_allow_otherwise(
        self, repo: Repository, alice
    ) -> None:
        """Several linked engagements, and the invariant holds across all of them."""
        for company in ("Revolut", "Monzo", "Starling"):
            _linked(repo, alice, company)
        assert repo.dangling_assessment_references() == []
