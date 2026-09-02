"""Deleting an assessment must not orphan an engagement (GRS-0246).

`delete_assessment` cascades carefully to everything referencing an assessment **by foreign key**.
An engagement references its assessments through `assessment_ids_json`, a JSON text column — no key,
no cascade, nothing to notice. Five staging engagements pointed at deleted assessments for a month
because of it, and that is what made the founder's duplicate rows undeletable: they defaulted to
`production` because nothing could be derived from an assessment that no longer existed.

ADR-0047 §4 already said orphaned references are the silent inconsistency #3 exists to prevent. The
guarantee just never reached the one relationship not expressed as a key.
"""

from __future__ import annotations

import json

import pytest
from bcap_contracts.assessments import RecordProvenance
from bcap_contracts.entities import PipelineStage

from grassmarket.data.models import AssessmentORM, EngagementORM
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
    eng_row = repo._session.get(EngagementORM, engagement.id)
    assert eng_row is not None
    eng_row.assessment_ids_json = json.dumps([str(assessment.id)])
    repo._session.flush()
    return assessment, engagement


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
        row = repo._session.get(EngagementORM, theirs.id)
        assert row is not None
        row.assessment_ids_json = json.dumps([str(assessment.id)])
        repo._session.flush()

        with pytest.raises(ConflictError):
            repo.delete_assessment(alice.principal, assessment.id, discard_scoring_runs=True)

    def test_a_partial_uuid_does_not_count_as_a_link(self, repo: Repository, alice) -> None:
        """Parsed, not substring-matched. A LIKE on raw JSON matches a partial UUID."""
        assessment = repo.create_assessment(
            alice.principal, subject="Solo", provenance=RecordProvenance.DEMO
        )
        prospect = repo.create_prospect(alice.principal, company_name="Other")
        for stage in _TO_CONTRACTED:
            prospect = repo.update_prospect_stage(alice.principal, prospect.id, stage)
        engagement = repo.create_engagement(
            alice.principal, prospect_id=prospect.id, title="Other — delivery"
        )
        row = repo._session.get(EngagementORM, engagement.id)
        assert row is not None
        row.assessment_ids_json = json.dumps([str(assessment.id)[:8]])  # a prefix, not the id
        repo._session.flush()
        repo.delete_assessment(alice.principal, assessment.id, discard_scoring_runs=True)


class TestTheStandingCheck:
    def test_a_clean_database_reports_nothing(self, repo: Repository, alice) -> None:
        _linked(repo, alice)
        assert repo.dangling_assessment_references() == []

    def test_it_finds_a_broken_link(self, repo: Repository, alice) -> None:
        """The state five staging engagements were in, reproduced."""
        assessment, engagement = _linked(repo, alice, "Revolut")
        # Deleted around the guard, exactly as the July cleanup did.
        repo._session.delete(repo._session.get(AssessmentORM, assessment.id))
        repo._session.flush()

        broken = repo.dangling_assessment_references()
        assert len(broken) == 1
        found_id, title, dead = broken[0]
        assert found_id == engagement.id
        assert title == "Revolut — delivery"
        assert dead == [str(assessment.id)]

    def test_it_reports_rather_than_repairs(self, repo: Repository, alice) -> None:
        """What to do about a dangling reference is a decision (ADR-0048), not a health check's."""
        assessment, _ = _linked(repo, alice)
        repo._session.delete(repo._session.get(AssessmentORM, assessment.id))
        repo._session.flush()
        repo.dangling_assessment_references()
        # Called twice: still reported, nothing quietly cleaned up in between.
        assert len(repo.dangling_assessment_references()) == 1
