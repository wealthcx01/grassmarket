"""An admin may act as another consultant, and it is recorded (GRS-0208, ADR-0041 adjacent).

The founder asked to review an advisor's work by *seeing exactly what that advisor sees*, which an
admin account cannot do — an admin sees everything and therefore shows nothing coherent.

The safety argument for the whole feature is one sentence, and most of this file exists to hold it
up: **act-as NARROWS, it never widens.** The principal it produces IS the subject — their id, their
role, their founder status — so `_assert_can_access` is untouched, every existing scoping test still
holds, and there is no path by which acting as someone shows more than being them would.

The other half is attribution. An act-as with no trace is impersonation; the difference between the
two is entirely the audit record, so the record carries both identities.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from bcap_contracts.audit import AuditEventType
from bcap_contracts.common import Role

from grassmarket.data.repository import (
    ConflictError,
    NotFoundError,
    Principal,
    Repository,
    ScopeViolationError,
)
from tests.conftest import SeededConsultant, auth_header

_NOW = datetime(2026, 8, 1, 12, 0, tzinfo=UTC)
_FOUNDER_EMAIL = "founder@bruntsfieldcapital.com"


def _act(repo: Repository, admin: SeededConsultant, subject: SeededConsultant) -> Principal:
    return repo.begin_act_as(
        admin.principal, subject.stored.id, now=_NOW, founder_reviewer_email=_FOUNDER_EMAIL
    )


class TestOnlyAnAdminMayStartIt:
    def test_a_consultant_cannot(
        self, repo: Repository, alice: SeededConsultant, bob: SeededConsultant
    ) -> None:
        with pytest.raises(ScopeViolationError):
            repo.begin_act_as(
                alice.principal, bob.stored.id, now=_NOW, founder_reviewer_email=_FOUNDER_EMAIL
            )

    def test_the_subject_must_exist(self, repo: Repository, admin: SeededConsultant) -> None:
        with pytest.raises(NotFoundError):
            repo.begin_act_as(
                admin.principal, uuid4(), now=_NOW, founder_reviewer_email=_FOUNDER_EMAIL
            )

    def test_acting_as_yourself_is_refused(self, repo: Repository, admin: SeededConsultant) -> None:
        """It would record a lie: an audit line saying an admin acted as someone, naming
        themselves."""
        with pytest.raises(ConflictError):
            repo.begin_act_as(
                admin.principal, admin.stored.id, now=_NOW, founder_reviewer_email=_FOUNDER_EMAIL
            )

    def test_chaining_from_a_consultant_session_is_refused_as_a_scope_violation(
        self,
        repo: Repository,
        admin: SeededConsultant,
        alice: SeededConsultant,
        bob: SeededConsultant,
    ) -> None:
        """Acting as A and then, from there, as B would leave the log ambiguous about who
        authorised the second hop.

        It is refused by the ADMIN check rather than the chaining check, and that ordering is worth
        pinning: while acting as a consultant the principal is not an admin at all, so the narrowing
        does the work before the specific guard is reached. The guard below still matters for the
        one case this does not cover.
        """
        acting = _act(repo, admin, alice)
        with pytest.raises(ScopeViolationError):
            repo.begin_act_as(
                acting, bob.stored.id, now=_NOW, founder_reviewer_email=_FOUNDER_EMAIL
            )

    def test_chaining_from_an_admin_session_is_refused_as_a_conflict(
        self, repo: Repository, admin: SeededConsultant, alice: SeededConsultant
    ) -> None:
        """The case the admin check cannot catch: an admin acting as ANOTHER ADMIN is still an
        admin, so only the explicit chaining guard stops the second hop."""
        acting_as_admin = Principal(
            consultant_id=admin.stored.id,
            role=Role.ADMIN,
            acting_admin_id=admin.stored.id,
        )
        with pytest.raises(ConflictError):
            repo.begin_act_as(
                acting_as_admin,
                alice.stored.id,
                now=_NOW,
                founder_reviewer_email=_FOUNDER_EMAIL,
            )


class TestItNarrowsAndNeverWidens:
    def test_the_principal_is_the_subject_not_an_admin_with_a_note(
        self, repo: Repository, admin: SeededConsultant, alice: SeededConsultant
    ) -> None:
        acting = _act(repo, admin, alice)
        assert acting.consultant_id == alice.stored.id
        assert acting.role is not Role.ADMIN
        # The load-bearing assertion of the whole feature. If this were True, act-as would be a way
        # to see MORE while claiming to see what one advisor sees.
        assert acting.is_admin is False
        assert acting.acting_admin_id == admin.stored.id

    def test_it_cannot_read_a_third_consultants_records(
        self,
        repo: Repository,
        admin: SeededConsultant,
        alice: SeededConsultant,
        bob: SeededConsultant,
    ) -> None:
        """An admin acting as Alice sees what Alice sees — which does not include Bob's work, even
        though the human driving is an admin who could have read it a moment earlier."""
        bobs = repo.create_prospect(bob.principal, company_name="Bob's Brokerage")
        acting = _act(repo, admin, alice)
        with pytest.raises(ScopeViolationError):
            repo.get_prospect(acting, bobs.id)
        # And the same admin, NOT acting, still can — the feature took nothing away.
        assert repo.get_prospect(admin.principal, bobs.id).id == bobs.id

    def test_it_sees_exactly_what_the_subject_sees(
        self, repo: Repository, admin: SeededConsultant, alice: SeededConsultant
    ) -> None:
        hers = repo.create_prospect(alice.principal, company_name="Alice's Brokerage")
        acting = _act(repo, admin, alice)
        assert repo.get_prospect(acting, hers.id).id == hers.id
        assert [p.id for p in repo.list_prospects(acting)] == [
            p.id for p in repo.list_prospects(alice.principal)
        ]

    def test_the_founder_claim_follows_the_subject_not_the_admin(
        self, repo: Repository, admin: SeededConsultant, alice: SeededConsultant
    ) -> None:
        """ADR-0041's gate is the one place where carrying the wrong claim does the most damage:
        an admin acting as an advisor must not be able to sign off what that advisor cannot."""
        acting = repo.begin_act_as(
            admin.principal, alice.stored.id, now=_NOW, founder_reviewer_email=alice.stored.email
        )
        assert acting.is_founder is True
        other = repo.begin_act_as(
            admin.principal,
            alice.stored.id,
            now=_NOW,
            founder_reviewer_email="someone.else@example.com",
        )
        assert other.is_founder is False


class TestItIsRecorded:
    def test_starting_writes_both_identities(
        self, repo: Repository, admin: SeededConsultant, alice: SeededConsultant
    ) -> None:
        _act(repo, admin, alice)
        events = repo.list_audit_events(admin.principal)
        started = [e for e in events if e.event_type is AuditEventType.ACT_AS_STARTED]
        assert len(started) == 1
        assert started[0].owner_consultant_id == admin.stored.id  # the actor is the ADMIN
        assert started[0].resource_id == alice.stored.id  # the subject is the resource
        assert str(admin.stored.id) in (started[0].detail or "")

    def test_ending_writes_a_bounded_interval(
        self, repo: Repository, admin: SeededConsultant, alice: SeededConsultant
    ) -> None:
        """'When did they stop' is as much a question as 'when did they start'."""
        acting = _act(repo, admin, alice)
        repo.end_act_as(acting, now=_NOW)
        events = repo.list_audit_events(admin.principal)
        assert any(e.event_type is AuditEventType.ACT_AS_ENDED for e in events)

    def test_ending_when_not_acting_is_refused(
        self, repo: Repository, admin: SeededConsultant
    ) -> None:
        with pytest.raises(ConflictError):
            repo.end_act_as(admin.principal, now=_NOW)

    def test_work_done_while_acting_names_the_admin_too(
        self, repo: Repository, admin: SeededConsultant, alice: SeededConsultant
    ) -> None:
        """No silent authorship. The work is Alice's; a named admin did it; the record says both,
        because dropping either half stops the log answering the question it exists for."""
        acting = _act(repo, admin, alice)
        repo.record_audit(
            actor_consultant_id=acting.consultant_id,
            event_type=AuditEventType.DELIVERABLE_GENERATED,
            now=_NOW,
            acting_admin_id=acting.acting_admin_id,
        )
        events = repo.list_audit_events(admin.principal)
        generated = next(e for e in events if e.event_type is AuditEventType.DELIVERABLE_GENERATED)
        assert str(admin.stored.id) in (generated.detail or "")
        assert str(alice.stored.id) in (generated.detail or "")


class TestOverTheApi:
    def test_an_admin_can_start_and_stop(
        self, client, admin: SeededConsultant, alice: SeededConsultant
    ) -> None:
        started = client.post(f"/auth/act-as/{alice.stored.id}", headers=auth_header(admin))
        assert started.status_code == 200, started.text
        body = started.json()
        assert body["subject_consultant_id"] == str(alice.stored.id)
        assert body["subject_email"] == alice.stored.email

        acting_header = {"Authorization": f"Bearer {body['access_token']}"}
        me = client.get("/auth/me", headers=acting_header)
        assert me.status_code == 200
        # The session reports the SUBJECT, which is what makes the banner honest.
        assert me.json()["id"] == str(alice.stored.id)

        stopped = client.delete("/auth/act-as", headers=acting_header)
        assert stopped.status_code == 200, stopped.text
        back = {"Authorization": f"Bearer {stopped.json()['access_token']}"}
        assert client.get("/auth/me", headers=back).json()["id"] == str(admin.stored.id)

    def test_a_consultant_is_refused(
        self, client, alice: SeededConsultant, bob: SeededConsultant
    ) -> None:
        refused = client.post(f"/auth/act-as/{bob.stored.id}", headers=auth_header(alice))
        assert refused.status_code == 403

    def test_an_act_as_session_cannot_read_a_third_advisor(
        self,
        client,
        admin: SeededConsultant,
        alice: SeededConsultant,
        bob: SeededConsultant,
    ) -> None:
        """The end-to-end version of the narrowing property, over HTTP rather than in-process."""
        created = client.post(
            "/prospects", json={"company_name": "Bob's Brokerage"}, headers=auth_header(bob)
        )
        assert created.status_code == 201, created.text
        bob_prospect = created.json()["id"]

        token = client.post(f"/auth/act-as/{alice.stored.id}", headers=auth_header(admin)).json()[
            "access_token"
        ]
        acting_header = {"Authorization": f"Bearer {token}"}
        assert client.get(f"/prospects/{bob_prospect}", headers=acting_header).status_code == 404
        # The same admin, not acting, still can.
        assert (
            client.get(f"/prospects/{bob_prospect}", headers=auth_header(admin)).status_code == 200
        )
