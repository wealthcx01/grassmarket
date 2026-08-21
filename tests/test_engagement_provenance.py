"""An engagement knows whether it describes real client work (GRS-0241 scope 1, ADR-0029).

The founder asked twice — 23/07 and 31/07 — for the duplicate demo rows on Engagements to go, and
it was never done. The reason turned out to be structural: **an engagement had no provenance**.
Assessments and deliverables carry one; engagements were the one owned record that did not. So
nothing could badge a demo engagement, and nothing could safely delete a duplicate one, because
ADR-0047 forbids deleting a production record and no engagement could be *shown* to be otherwise.

The derivation is the load-bearing part. An engagement drawing on a demo assessment is itself demo,
and that cannot be forged, because assessment provenance is already immutable and already
unforgeable. It gives the demo seed the right answer without opening a field a request could lie in
— ADR-0029's rule being that a DEMO marker is never accepted from a client.
"""

from __future__ import annotations

import pytest
from bcap_contracts.assessments import AssessmentState, RecordProvenance
from bcap_contracts.entities import PipelineStage

from grassmarket.data.models import AssessmentORM
from grassmarket.data.repository import Repository

_TO_CONTRACTED = (
    PipelineStage.WORKSHOP_SCHEDULED,
    PipelineStage.WORKSHOP_DELIVERED,
    PipelineStage.QUALIFIED,
    PipelineStage.SCOPED,
    PipelineStage.CONTRACTED,
)


def _contracted(repo: Repository, owner, company: str = "Acme"):
    prospect = repo.create_prospect(owner.principal, company_name=company)
    for stage in _TO_CONTRACTED:
        prospect = repo.update_prospect_stage(owner.principal, prospect.id, stage)
    return prospect


def _finalised(repo: Repository, owner, subject: str, provenance: RecordProvenance):
    assessment = repo.create_assessment(owner.principal, subject=subject, provenance=provenance)
    row = repo._session.get(AssessmentORM, assessment.id)
    assert row is not None
    row.state = AssessmentState.FINALISED.value
    row.subject = subject
    repo._session.flush()
    return repo.get_assessment(owner.principal, assessment.id)


def test_an_engagement_defaults_to_production(repo: Repository, alice) -> None:
    """The safe direction: an engagement nobody marked is treated as real client work."""
    prospect = _contracted(repo, alice)
    engagement = repo.create_engagement(alice.principal, prospect_id=prospect.id, title="E")
    assert engagement.provenance is RecordProvenance.PRODUCTION


def test_a_demo_assessment_makes_the_engagement_demo(repo: Repository, alice) -> None:
    """The derivation. This is how the demo seed gets the right answer over HTTP."""
    prospect = _contracted(repo, alice)
    demo = _finalised(repo, alice, "Acme", RecordProvenance.DEMO)
    engagement = repo.create_engagement(
        alice.principal, prospect_id=prospect.id, title="E", assessment_ids=(demo.id,)
    )
    assert engagement.provenance is RecordProvenance.DEMO


def test_a_sandbox_assessment_makes_the_engagement_sandbox(repo: Repository, alice) -> None:
    prospect = _contracted(repo, alice)
    sandbox = _finalised(repo, alice, "Acme", RecordProvenance.SANDBOX)
    engagement = repo.create_engagement(
        alice.principal, prospect_id=prospect.id, title="E", assessment_ids=(sandbox.id,)
    )
    assert engagement.provenance is RecordProvenance.SANDBOX


def test_a_production_assessment_leaves_it_production(repo: Repository, alice) -> None:
    prospect = _contracted(repo, alice)
    real = _finalised(repo, alice, "Acme", RecordProvenance.PRODUCTION)
    engagement = repo.create_engagement(
        alice.principal, prospect_id=prospect.id, title="E", assessment_ids=(real.id,)
    )
    assert engagement.provenance is RecordProvenance.PRODUCTION


def test_the_derivation_can_only_ever_mark_more_never_less(repo: Repository, alice) -> None:
    """A caller asking for DEMO on production assessments does not get PRODUCTION back.

    The rule is one-directional on purpose: a marker can be strengthened by what the record draws
    on, never weakened. If this ever inverted, linking a real assessment would quietly un-badge a
    demo engagement — and an un-badged demo record is precisely what ADR-0029 exists to prevent.
    """
    prospect = _contracted(repo, alice)
    real = _finalised(repo, alice, "Acme", RecordProvenance.PRODUCTION)
    engagement = repo.create_engagement(
        alice.principal,
        prospect_id=prospect.id,
        title="E",
        assessment_ids=(real.id,),
        provenance=RecordProvenance.DEMO,
    )
    assert engagement.provenance is RecordProvenance.DEMO


@pytest.mark.parametrize(
    "provenance", [RecordProvenance.PRODUCTION, RecordProvenance.DEMO, RecordProvenance.SANDBOX]
)
def test_provenance_survives_a_round_trip(
    repo: Repository, alice, provenance: RecordProvenance
) -> None:
    """It has to be readable back, or the badge and the cleanup script both read nothing."""
    prospect = _contracted(repo, alice)
    created = repo.create_engagement(
        alice.principal, prospect_id=prospect.id, title="E", provenance=provenance
    )
    assert repo.get_engagement(alice.principal, created.id).provenance is provenance


class TestDeletionCannotTouchProduction:
    """ADR-0047, applied to engagements. The guard is in the repository, not the script."""

    def test_a_production_engagement_refuses_deletion(self, repo: Repository, alice) -> None:
        from grassmarket.data.repository import ScopeViolationError

        prospect = _contracted(repo, alice)
        engagement = repo.create_engagement(alice.principal, prospect_id=prospect.id, title="Real")
        with pytest.raises(ScopeViolationError):
            repo.delete_engagement(alice.principal, engagement.id)
        # And it is still there — the refusal is not a partial delete.
        assert repo.get_engagement(alice.principal, engagement.id).title == "Real"

    def test_a_demo_engagement_deletes(self, repo: Repository, alice) -> None:
        from grassmarket.data.repository import NotFoundError

        prospect = _contracted(repo, alice)
        demo = _finalised(repo, alice, "Acme", RecordProvenance.DEMO)
        engagement = repo.create_engagement(
            alice.principal, prospect_id=prospect.id, title="Demo", assessment_ids=(demo.id,)
        )
        repo.delete_engagement(alice.principal, engagement.id)
        with pytest.raises(NotFoundError):
            repo.get_engagement(alice.principal, engagement.id)

    def test_another_advisors_demo_engagement_is_not_found(
        self, repo: Repository, alice, bob
    ) -> None:
        """Scoping first, provenance second: a cross-owner row is not even reported as demo."""
        from grassmarket.data.repository import NotFoundError, ScopeViolationError

        prospect = _contracted(repo, alice)
        demo = _finalised(repo, alice, "Acme", RecordProvenance.DEMO)
        engagement = repo.create_engagement(
            alice.principal, prospect_id=prospect.id, title="Demo", assessment_ids=(demo.id,)
        )
        with pytest.raises((NotFoundError, ScopeViolationError)):
            repo.delete_engagement(bob.principal, engagement.id)


class TestOrphanedEngagementRemoval:
    """ADR-0048. Every condition, asserted — this path must never become a general escape hatch."""

    def _orphaned(self, repo: Repository, alice, title: str = "Orphan"):
        """An engagement whose only linked assessment is then deleted out from under it."""
        prospect = _contracted(repo, alice, title)
        assessment = _finalised(repo, alice, title, RecordProvenance.DEMO)
        engagement = repo.create_engagement(
            alice.principal,
            prospect_id=prospect.id,
            title=title,
            assessment_ids=(assessment.id,),
        )
        repo._session.delete(repo._session.get(AssessmentORM, assessment.id))
        repo._session.flush()
        return engagement

    def test_it_removes_a_genuine_orphan(self, repo: Repository, alice) -> None:
        from grassmarket.data.repository import NotFoundError

        engagement = self._orphaned(repo, alice)
        repo.delete_orphaned_engagement(alice.principal, engagement.id, founder_authorised=True)
        with pytest.raises(NotFoundError):
            repo.get_engagement(alice.principal, engagement.id)

    def test_it_refuses_without_authorisation(self, repo: Repository, alice) -> None:
        """Named so it cannot be set absent-mindedly, and defaulting to refuse."""
        from grassmarket.data.repository import ScopeViolationError

        engagement = self._orphaned(repo, alice)
        with pytest.raises(ScopeViolationError):
            repo.delete_orphaned_engagement(alice.principal, engagement.id)

    def test_it_refuses_an_engagement_that_links_nothing(self, repo: Repository, alice) -> None:
        """Not orphaned — just new. Deleting it would remove work in progress."""
        from grassmarket.data.repository import EngagementLinkError

        prospect = _contracted(repo, alice)
        engagement = repo.create_engagement(alice.principal, prospect_id=prospect.id, title="New")
        with pytest.raises(EngagementLinkError):
            repo.delete_orphaned_engagement(alice.principal, engagement.id, founder_authorised=True)

    def test_it_refuses_when_any_link_still_resolves(self, repo: Repository, alice) -> None:
        """A partly-dangling engagement is a link to REPAIR, not an orphan to delete."""
        from grassmarket.data.repository import EngagementLinkError

        prospect = _contracted(repo, alice)
        dead = _finalised(repo, alice, "Acme", RecordProvenance.DEMO)
        live = _finalised(repo, alice, "Acme", RecordProvenance.DEMO)
        engagement = repo.create_engagement(
            alice.principal,
            prospect_id=prospect.id,
            title="Half",
            assessment_ids=(dead.id, live.id),
        )
        repo._session.delete(repo._session.get(AssessmentORM, dead.id))
        repo._session.flush()
        with pytest.raises(EngagementLinkError):
            repo.delete_orphaned_engagement(alice.principal, engagement.id, founder_authorised=True)

    def test_it_refuses_an_orphan_that_produced_deliverables(self, repo: Repository, alice) -> None:
        """Produced output may have reached a client, whatever the links now say."""
        from bcap_contracts.engagements import DeliverableSlot

        from grassmarket.data.repository import EngagementLinkError

        prospect = _contracted(repo, alice)
        assessment = _finalised(repo, alice, "Acme", RecordProvenance.DEMO)
        engagement = repo.create_engagement(
            alice.principal,
            prospect_id=prospect.id,
            title="Produced",
            assessment_ids=(assessment.id,),
            deliverables=(DeliverableSlot(key="roadmap"),),
        )
        repo._session.delete(repo._session.get(AssessmentORM, assessment.id))
        repo._session.flush()
        with pytest.raises(EngagementLinkError):
            repo.delete_orphaned_engagement(alice.principal, engagement.id, founder_authorised=True)

    def test_another_advisors_orphan_is_not_reachable(self, repo: Repository, alice, bob) -> None:
        """Scoping is still first. Founder authorisation is not a cross-owner key."""
        from grassmarket.data.repository import NotFoundError, ScopeViolationError

        engagement = self._orphaned(repo, alice)
        with pytest.raises((NotFoundError, ScopeViolationError)):
            repo.delete_orphaned_engagement(bob.principal, engagement.id, founder_authorised=True)
