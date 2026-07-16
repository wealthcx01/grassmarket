"""Audit log + GDPR compliance (GRS-0032).

The append-only audit log covers every listed event class and is admin-only; GDPR export bundles a
person's footprint; erasure removes personal data but keeps immutable scoring runs, anonymised.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from bcap_contracts.audit import AuditEventType
from bcap_contracts.commissions import DeliveryType, SourcingAttribution
from bcap_contracts.money import Currency, Money
from cryptography.fernet import Fernet

from grassmarket.data.models import MeetingTranscriptORM, ProspectORM, ScoringRunORM
from grassmarket.data.repository import Repository, ScopeViolationError
from grassmarket.pathb.cipher import FernetTranscriptCipher
from tests.conftest import SeededConsultant, auth_header
from tests.test_scoring_run_persistence import _create

_NOW = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)


# --- Audit log -----------------------------------------------------------------------------


def test_the_audit_log_covers_every_listed_event_class(
    repo: Repository, admin: SeededConsultant
) -> None:
    # Record one of every event class, then confirm the (admin-only) log returns them all.
    for event_type in AuditEventType:
        repo.record_audit(
            actor_consultant_id=admin.principal.consultant_id, event_type=event_type, now=_NOW
        )
    events = repo.list_audit_events(admin.principal)
    assert {e.event_type for e in events} == set(AuditEventType)


def test_the_audit_log_is_admin_only(repo: Repository, alice: SeededConsultant) -> None:
    with pytest.raises(ScopeViolationError, match="admin"):
        repo.list_audit_events(alice.principal)


def test_audit_log_is_paginated_newest_first(repo: Repository, admin: SeededConsultant) -> None:
    """GRS-0050: the append-only log must never return unbounded. A limit caps the page and a
    hostile over-limit is clamped, not honoured; ordering is newest-first for a useful page."""
    for i in range(10):
        repo.record_audit(
            actor_consultant_id=admin.principal.consultant_id,
            event_type=AuditEventType.AUTH_LOGIN,
            now=datetime(2026, 7, 14, 12, i, tzinfo=UTC),
        )
    page = repo.list_audit_events(admin.principal, limit=3)
    assert len(page) == 3
    assert page[0].at >= page[1].at >= page[2].at  # newest first
    # offset walks the pages; an over-limit request is clamped to MAX_PAGE_LIMIT, never unbounded.
    next_page = repo.list_audit_events(admin.principal, limit=3, offset=3)
    assert {e.id for e in page}.isdisjoint({e.id for e in next_page})
    assert len(repo.list_audit_events(admin.principal, limit=10_000)) <= 500


def test_audit_endpoint_rejects_out_of_range_limit(client, admin: SeededConsultant) -> None:
    assert client.get("/compliance/audit?limit=0", headers=auth_header(admin)).status_code == 422
    assert (
        client.get("/compliance/audit?limit=99999", headers=auth_header(admin)).status_code == 422
    )
    assert client.get("/compliance/audit?limit=50", headers=auth_header(admin)).status_code == 200


def test_login_is_audited(client, alice: SeededConsultant, admin: SeededConsultant) -> None:
    resp = client.post(
        "/auth/login",
        json={"email": alice.stored.email, "password": "correct-horse-battery-staple"},
    )
    assert resp.status_code == 200, resp.text
    log = client.get("/compliance/audit", headers=auth_header(admin)).json()
    assert any(
        e["event_type"] == "auth_login" and e["resource_id"] == str(alice.stored.id) for e in log
    )


def test_recording_a_commission_is_audited(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    repo.record_consultancy_commission(
        admin.principal,
        advisor_id=alice.stored.id,
        engagement_id=alice.stored.id,  # any uuid — informational
        base_value=Money(
            amount_minor=4_000_000, currency=Currency.GBP, assumption_register_ref="c"
        ),
        sourcing=SourcingAttribution.SELF_SOURCED,
        delivery_type=DeliveryType.BRUNTSFIELD_LED,
        contract_year=1,
        earned_on=_NOW.date(),
    )
    assert any(
        e.event_type is AuditEventType.COMMISSION_RECORDED
        for e in repo.list_audit_events(admin.principal)
    )


# --- GDPR export ---------------------------------------------------------------------------


def _seed_footprint(repo: Repository, owner: SeededConsultant) -> None:
    repo.create_prospect(owner.principal, company_name="Meridian Securities")
    repo.ingest_pasted_transcript(
        owner.principal,
        text="a confidential call",
        source_filename="call.txt",
        cipher=FernetTranscriptCipher(Fernet.generate_key().decode()),
    )


def test_export_bundles_a_persons_whole_footprint(
    repo: Repository, alice: SeededConsultant
) -> None:
    _seed_footprint(repo, alice)
    export = repo.export_personal_data(alice.principal, alice.stored.id, now=_NOW)

    assert export.subject_consultant_id == alice.stored.id
    # The consultant record is present with the password hash REDACTED.
    assert export.records["consultant"][0]["hashed_password"] == "[redacted]"
    # Owned resources are bundled by table.
    assert export.records["prospects"][0]["company_name"] == "Meridian Securities"
    assert len(export.records["meeting_transcripts"]) == 1
    # The transcript ciphertext is not dumped raw.
    assert export.records["meeting_transcripts"][0]["text_ciphertext"] == "[encrypted]"


def test_export_is_self_or_admin(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    with pytest.raises(ScopeViolationError):
        repo.export_personal_data(bob.principal, alice.stored.id, now=_NOW)


# --- GDPR erasure --------------------------------------------------------------------------


def test_erasure_removes_personal_data_but_keeps_anonymised_runs(
    repo: Repository, alice: SeededConsultant, session_factory
) -> None:
    _seed_footprint(repo, alice)
    run = _create(repo, alice)  # an immutable scoring run
    run_id = run.id

    counts = repo.delete_personal_data(alice.principal, alice.stored.id, now=_NOW)
    assert counts["prospects"] == 1
    assert counts["meeting_transcripts"] == 1

    # Verify against the raw tables in a fresh session.
    session = session_factory()
    try:
        from sqlalchemy import select

        # The personal data is gone…
        assert (
            session.execute(
                select(ProspectORM).where(ProspectORM.owner_consultant_id == alice.stored.id)
            ).first()
            is None
        )
        assert (
            session.execute(
                select(MeetingTranscriptORM).where(
                    MeetingTranscriptORM.owner_consultant_id == alice.stored.id
                )
            ).first()
            is None
        )
        # …the consultant is anonymised (no PII, id kept)…
        from grassmarket.data.models import ConsultantORM

        consultant = session.get(ConsultantORM, alice.stored.id)
        assert consultant is not None
        assert consultant.full_name == "[deleted]"
        assert "anonymised.invalid" in consultant.email
        assert consultant.is_active is False
        # …and the immutable scoring run SURVIVES (de-identified — owner is now anonymised).
        surviving = session.get(ScoringRunORM, run_id)
        assert surviving is not None
    finally:
        session.close()


def test_erasure_scrubs_the_subjects_invitation_pii(
    repo: Repository, alice: SeededConsultant, session_factory
) -> None:
    from datetime import timedelta

    from bcap_contracts.common import ConsultantTier, Role

    from grassmarket.data.models import InvitationORM

    # An invitation carrying the subject's email lives in a table with NO owner_consultant_id —
    # reflection-based deletion would miss it. Erasure must scrub it anyway.
    repo.create_invitation(
        email=alice.stored.email,
        token_hash="hash1",
        role=Role.CONSULTANT,
        tier=ConsultantTier.VENTURE_ASSOCIATE,
        invited_by_consultant_id=alice.stored.id,
        expires_at=_NOW + timedelta(days=7),
    )
    repo.delete_personal_data(alice.principal, alice.stored.id, now=_NOW)

    session = session_factory()
    try:
        from sqlalchemy import select

        assert (
            session.execute(
                select(InvitationORM).where(InvitationORM.email == alice.stored.email)
            ).first()
            is None
        )
    finally:
        session.close()


def test_erasure_removes_a_cross_owner_draft_on_the_subjects_assessment(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant, session_factory
) -> None:
    # Dual rating: BOB (a second rater) has a draft on ALICE's assessment. The draft is owned by bob
    # but FK-references alice's assessment. Erasing alice must remove it — else deleting alice's
    # assessment orphans the FK and aborts the whole erasure on Postgres (the P1 the review found).
    from grassmarket.data.models import ModuleRatingDraftORM

    assessment = repo.create_assessment(alice.principal, subject="Meridian")
    session = session_factory()
    try:
        session.add(
            ModuleRatingDraftORM(
                owner_consultant_id=bob.stored.id,  # owned by the co-rater, not the subject
                assessment_id=assessment.id,
                module_key="APP_SERVER",
                ratings_json="[]",
            )
        )
        session.commit()
    finally:
        session.close()

    counts = repo.delete_personal_data(alice.principal, alice.stored.id, now=_NOW)
    assert counts["module_rating_drafts"] >= 1

    check = session_factory()
    try:
        from sqlalchemy import select

        assert (
            check.execute(
                select(ModuleRatingDraftORM).where(
                    ModuleRatingDraftORM.assessment_id == assessment.id
                )
            ).first()
            is None
        )
    finally:
        check.close()


def test_export_includes_the_subjects_invitation(repo: Repository, alice: SeededConsultant) -> None:
    from datetime import timedelta

    from bcap_contracts.common import ConsultantTier, Role

    repo.create_invitation(
        email=alice.stored.email,
        token_hash="secret-hash",
        role=Role.CONSULTANT,
        tier=ConsultantTier.VENTURE_ASSOCIATE,
        invited_by_consultant_id=alice.stored.id,
        expires_at=_NOW + timedelta(days=7),
    )
    export = repo.export_personal_data(alice.principal, alice.stored.id, now=_NOW)
    invites = export.records["invitations"]
    assert len(invites) == 1
    assert invites[0]["email"] == alice.stored.email
    assert invites[0]["token_hash"] == "[redacted]"  # the secret is not dumped


def test_erasure_is_audited(
    repo: Repository, alice: SeededConsultant, admin: SeededConsultant
) -> None:
    repo.delete_personal_data(admin.principal, alice.stored.id, now=_NOW)
    assert any(
        e.event_type is AuditEventType.GDPR_DELETION
        for e in repo.list_audit_events(admin.principal)
    )


def test_erasure_is_self_or_admin(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    with pytest.raises(ScopeViolationError):
        repo.delete_personal_data(bob.principal, alice.stored.id, now=_NOW)
