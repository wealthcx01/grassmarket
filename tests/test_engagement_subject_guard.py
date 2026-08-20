"""Linking an assessment to the wrong firm's engagement (GRS-0241 scope 4).

Until now `link_assessment_to_engagement` checked ownership, finalisation and duplication — and
never that the assessment was *about* the engagement's client. The detail page offered a dropdown of
every finalised assessment the advisor owned, so one click linked Deutsche Börse's scores to the
WeBull engagement, and nothing anywhere said otherwise.

The deliverable generated from that link carries one firm's name over another firm's numbers. That
is the worst output this system can produce, and it was a click away.

These tests hold three things: it refuses by default, the refusal names both firms, and the override
cannot happen by accident.
"""

from __future__ import annotations

import pytest
from bcap_contracts.entities import PipelineStage

from grassmarket.data.repository import (
    EngagementLinkError,
    EngagementSubjectMismatchError,
    Repository,
    _loose_name,
)

_TO_CONTRACTED = (
    PipelineStage.WORKSHOP_SCHEDULED,
    PipelineStage.WORKSHOP_DELIVERED,
    PipelineStage.QUALIFIED,
    PipelineStage.SCOPED,
    PipelineStage.CONTRACTED,
)


def _engagement_for(repo: Repository, owner, company: str):
    prospect = repo.create_prospect(owner.principal, company_name=company)
    for stage in _TO_CONTRACTED:
        prospect = repo.update_prospect_stage(owner.principal, prospect.id, stage)
    return repo.create_engagement(
        owner.principal, prospect_id=prospect.id, title=f"{company} — delivery"
    )


def _finalised_assessment_about(repo: Repository, owner, subject: str):
    """A finalised assessment about `subject`.

    The state is set directly on the ORM row rather than driven through submit → founder-approve →
    finalise. That flow is thoroughly covered elsewhere and needs a founder principal and an HTTP
    client; what these tests are about is the check that sits AFTER finalisation, and routing
    through the whole gate would make the fixture the subject of the test.
    """
    from bcap_contracts.assessments import AssessmentState

    from grassmarket.data.models import AssessmentORM

    assessment = repo.create_assessment(owner.principal, subject=subject)
    row = repo._session.get(AssessmentORM, assessment.id)
    assert row is not None
    row.state = AssessmentState.FINALISED.value
    row.subject = subject
    repo._session.flush()
    return repo.get_assessment(owner.principal, assessment.id)


@pytest.fixture
def engagement_fixture(repo: Repository, alice):
    """A WeBull engagement, and a finalised assessment about a different firm entirely."""
    engagement = _engagement_for(repo, alice, "WeBull")
    other = _finalised_assessment_about(repo, alice, "Deutsche Börse")
    return repo, alice.principal, engagement, other


def test_a_matching_subject_links_without_confirmation(repo: Repository, alice) -> None:
    """The guard must not become an obstacle on the normal path."""
    engagement = _engagement_for(repo, alice, "WeBull")
    own = _finalised_assessment_about(repo, alice, "WeBull")
    linked = repo.link_assessment_to_engagement(alice.principal, engagement.id, own.id)
    assert str(own.id) in [str(a) for a in linked.assessment_ids]


def test_a_blank_subject_never_refuses(repo: Repository, alice) -> None:
    """A blank subject is an absence of evidence, not a mismatch.

    Refusing on it would block a legitimate link with a message naming nothing.
    """
    engagement = _engagement_for(repo, alice, "WeBull")
    blank = _finalised_assessment_about(repo, alice, "")
    repo.link_assessment_to_engagement(alice.principal, engagement.id, blank.id)


class TestTheGuardRefusesByDefault:
    def test_a_different_firm_is_refused(self, engagement_fixture) -> None:
        repo, principal, engagement, other_assessment = engagement_fixture
        with pytest.raises(EngagementSubjectMismatchError):
            repo.link_assessment_to_engagement(principal, engagement.id, other_assessment.id)

    def test_the_refusal_names_both_firms(self, engagement_fixture) -> None:
        """A refusal an advisor cannot act on is only half a guard."""
        repo, principal, engagement, other_assessment = engagement_fixture
        with pytest.raises(EngagementSubjectMismatchError) as exc:
            repo.link_assessment_to_engagement(principal, engagement.id, other_assessment.id)
        message = str(exc.value)
        assert "WeBull" in message
        assert "Deutsche" in message

    def test_it_says_what_would_go_wrong_not_merely_that_it_refused(
        self, engagement_fixture
    ) -> None:
        repo, principal, engagement, other_assessment = engagement_fixture
        with pytest.raises(EngagementSubjectMismatchError) as exc:
            repo.link_assessment_to_engagement(principal, engagement.id, other_assessment.id)
        assert "deliverable" in str(exc.value).lower()

    def test_it_is_an_EngagementLinkError_so_older_callers_still_refuse(
        self, engagement_fixture
    ) -> None:
        """The subclass is the point: code written before this check keeps failing safe."""
        repo, principal, engagement, other_assessment = engagement_fixture
        with pytest.raises(EngagementLinkError):
            repo.link_assessment_to_engagement(principal, engagement.id, other_assessment.id)


class TestTheOverrideIsDeliberate:
    def test_confirming_links_it(self, engagement_fixture) -> None:
        repo, principal, engagement, other_assessment = engagement_fixture
        linked = repo.link_assessment_to_engagement(
            principal, engagement.id, other_assessment.id, confirm_subject_mismatch=True
        )
        assert str(other_assessment.id) in [str(a) for a in linked.assessment_ids]

    def test_the_default_is_refuse(self, engagement_fixture) -> None:
        """If this ever flips, every caller that omits the flag silently starts cross-wiring."""
        import inspect

        from grassmarket.data.repository import Repository

        signature = inspect.signature(Repository.link_assessment_to_engagement)
        assert signature.parameters["confirm_subject_mismatch"].default is False


class TestTheMatchIsLooseInTheSafeDirection:
    """The guard must catch two different firms without policing spelling."""

    @pytest.mark.parametrize(
        ("client", "subject"),
        [
            ("WeBull", "WeBull"),
            ("WeBull", "webull"),
            ("Deutsche Börse", "Deutsche Borse"),  # punctuation and accents
            ("WeBull", "WeBull Financial LLC"),  # a longer legal name
            ("Hargreaves Lansdown plc", "Hargreaves Lansdown"),
            ("WeBull", ""),  # a blank subject is an absence of evidence, not a mismatch
        ],
    )
    def test_these_are_not_mismatches(self, repo, alice, client: str, subject: str) -> None:

        if not subject:
            pytest.skip("covered by test_a_blank_subject_never_refuses")
        assert _loose_name(client) in _loose_name(subject) or _loose_name(subject) in _loose_name(
            client
        )

    @pytest.mark.parametrize(
        ("client", "subject"),
        [("WeBull", "Deutsche Börse"), ("Revolut", "Hargreaves Lansdown")],
    )
    def test_these_are_mismatches(self, client: str, subject: str) -> None:

        a, b = _loose_name(client), _loose_name(subject)
        assert a != b and a not in b and b not in a
