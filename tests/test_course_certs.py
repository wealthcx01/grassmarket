"""Course / product certification tests (GRS-0127).

The acceptance: a Sales Egoist cert and a per-product cert exist alongside the assessor ladder and
reuse `CertificationRecord`/`CertificationEvent` (no parallel store); course-cert progress is gated
like the ladder; and certification requires the senior↔junior pairing — a senior sign-off that is
NOT the learner, on a completed course.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from bcap_contracts.certification import CertificationEventKind, CourseCertificationStatus
from bcap_contracts.common import AssessorLevel

from grassmarket.data.repository import ConflictError, Repository, ScopeViolationError
from grassmarket.workbench.content.seed import seed_academy_content
from grassmarket.workbench.course_certs import (
    SALES_EGOIST_SUBJECT,
    course_cert_status,
    course_cert_subjects,
    signoff_blockers,
)
from tests.conftest import SeededConsultant, auth_header

_NOW = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


# ---------------------------------------------------------------- pure logic
def test_subjects_are_sales_egoist_plus_one_per_product() -> None:
    subjects = course_cert_subjects(["openbb", "connecttrade"])
    keys = [s.key for s in subjects]
    assert keys[0] == SALES_EGOIST_SUBJECT
    assert "product:openbb" in keys and "product:connecttrade" in keys


def test_underscore_product_ids_get_a_valid_hyphenated_backing_slug() -> None:
    # Course slugs forbid underscores; a product_id like 'brandfetch_distribution' must map to a
    # hyphenated backing slug or its cert could never be earned (GRS-0125 fix).
    subjects = {s.key: s for s in course_cert_subjects(["brandfetch_distribution"])}
    subj = subjects["product:brandfetch_distribution"]
    assert subj.backing_slug == "product-brandfetch-distribution"
    assert "_" not in subj.backing_slug


def test_status_folds_completion_and_signoff() -> None:
    assert (
        course_cert_status(course_complete=False, has_signoff=False)
        is CourseCertificationStatus.NOT_STARTED
    )
    assert (
        course_cert_status(course_complete=True, has_signoff=False)
        is CourseCertificationStatus.IN_PROGRESS
    )
    assert (
        course_cert_status(course_complete=True, has_signoff=True)
        is CourseCertificationStatus.CERTIFIED
    )


def test_signoff_blockers_enforce_the_pairing() -> None:
    # A complete course, signed by a different senior → no blockers.
    assert (
        signoff_blockers(course_complete=True, signer_is_senior=True, signer_is_learner=False) == []
    )
    # Self-signoff is refused (that's self-report, not pairing).
    assert signoff_blockers(course_complete=True, signer_is_senior=True, signer_is_learner=True)
    # A non-senior signer is refused.
    assert signoff_blockers(course_complete=True, signer_is_senior=False, signer_is_learner=False)
    # An incomplete course is refused.
    assert signoff_blockers(course_complete=False, signer_is_senior=True, signer_is_learner=False)


# ---------------------------------------------------------------- repository (reuses the audit)
def _complete_sales_egoist(repo: Repository, learner: SeededConsultant) -> None:
    published = repo.get_published_course(learner.principal, "sales-egoist")
    for module in published.tree.modules:
        for lesson in module.lessons:
            repo.complete_lesson(learner.principal, "sales-egoist", lesson.id, now=_NOW)


def test_course_cert_lifecycle_through_the_pairing(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)  # publishes Sales Egoist

    # Before any coursework: NOT_STARTED.
    certs = {
        c.subject: c
        for c in repo.list_course_certifications(alice.principal, alice.principal.consultant_id)
    }
    assert certs[SALES_EGOIST_SUBJECT].status is CourseCertificationStatus.NOT_STARTED

    # Complete the course → IN_PROGRESS (awaiting the pairing sign-off).
    _complete_sales_egoist(repo, alice)
    in_prog = repo.list_course_certifications(alice.principal, alice.principal.consultant_id)
    assert (
        next(c for c in in_prog if c.subject == SALES_EGOIST_SUBJECT).status
        is CourseCertificationStatus.IN_PROGRESS
    )

    # A senior (admin here) signs off → CERTIFIED, recorded via a CertificationEvent (no new store).
    cert = repo.signoff_course_certification(
        admin.principal, alice.principal.consultant_id, SALES_EGOIST_SUBJECT, now=_NOW
    )
    assert cert.status is CourseCertificationStatus.CERTIFIED
    assert cert.signed_off_by_consultant_id == admin.principal.consultant_id

    events = repo.list_certification_events(alice.principal, alice.principal.consultant_id)
    signoffs = [
        e
        for e in events
        if e.kind is CertificationEventKind.SIGNOFF_RECORDED
        and e.cert_subject == SALES_EGOIST_SUBJECT
    ]
    assert len(signoffs) == 1  # the same audit store the ladder uses


def test_cannot_self_sign_or_sign_incomplete(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    # Course not complete → refused even by a senior.
    with pytest.raises(ConflictError):
        repo.signoff_course_certification(
            admin.principal, alice.principal.consultant_id, SALES_EGOIST_SUBJECT, now=_NOW
        )
    # Complete it, then a self-signoff by the learner is refused (pairing, not self-report).
    _complete_sales_egoist(repo, alice)
    with pytest.raises(ConflictError):
        repo.signoff_course_certification(
            alice.principal, alice.principal.consultant_id, SALES_EGOIST_SUBJECT, now=_NOW
        )


def test_non_senior_cannot_sign_off(
    repo: Repository, admin: SeededConsultant, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    _complete_sales_egoist(repo, alice)
    # Bob is a plain consultant (TRAINED), not a Certified Lead → refused.
    assert bob.stored.assessor_level is not AssessorLevel.CERTIFIED_LEAD
    with pytest.raises(ConflictError):
        repo.signoff_course_certification(
            bob.principal, alice.principal.consultant_id, SALES_EGOIST_SUBJECT, now=_NOW
        )


def test_course_certs_are_owner_scoped(
    repo: Repository, alice: SeededConsultant, bob: SeededConsultant
) -> None:
    with pytest.raises(ScopeViolationError):
        repo.list_course_certifications(alice.principal, bob.principal.consultant_id)


# ---------------------------------------------------------------- HTTP surface
def test_http_list_and_signoff(
    client, repo: Repository, admin: SeededConsultant, alice: SeededConsultant
) -> None:
    seed_academy_content(repo, admin.principal, now=_NOW)
    _complete_sales_egoist(repo, alice)
    repo._session.commit()  # make the seed visible to the app's request sessions

    mine = client.get("/workbench/certifications/course", headers=auth_header(alice))
    assert mine.status_code == 200
    assert any(c["subject"] == SALES_EGOIST_SUBJECT for c in mine.json())

    signed = client.post(
        "/workbench/certifications/course/signoff",
        json={
            "learner_consultant_id": str(alice.principal.consultant_id),
            "subject": SALES_EGOIST_SUBJECT,
        },
        headers=auth_header(admin),
    )
    assert signed.status_code == 200
    assert signed.json()["status"] == "certified"
