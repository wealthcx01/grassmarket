"""Course/product certification logic (GRS-0127) — pure helpers over the certification events.

The Academy adds a **Sales Egoist cert + one cert per product** on top of the assessor ladder,
reusing the same `CertificationEvent` audit (no parallel store) — a course cert is folded from the
events whose `cert_subject` matches. Certification requires the backing course complete AND a
**senior sign-off that is not the learner** — the senior↔junior pairing, never self-report.

Everything here is pure (no persistence, no clock); the repository composes it.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from bcap_contracts.certification import CourseCertificationStatus

SALES_EGOIST_SUBJECT = "sales_egoist"
_PRODUCT_PREFIX = "product:"


@dataclass(frozen=True)
class CourseCertSubject:
    """A certifiable subject: its stable key, display title, and the slug of the course whose
    completion is the evidence."""

    key: str
    title: str
    backing_slug: str


def product_subject_key(product_id: str) -> str:
    return f"{_PRODUCT_PREFIX}{product_id}"


def _product_backing_slug(product_id: str) -> str:
    """The course slug that backs a product cert. Course slugs forbid underscores
    (`^[a-z0-9][a-z0-9-]*$`), so a product_id like `brandfetch_distribution` is hyphenated —
    otherwise its cert could never be earned (no valid course slug could match)."""
    return f"product-{product_id.replace('_', '-')}"


def course_cert_subjects(product_ids: Iterable[str]) -> list[CourseCertSubject]:
    """The full certifiable set: Sales Egoist first, then one per catalogue product (stable order).
    Backing slugs match the seeded course slugs (`sales-egoist`, `product-<id>`, hyphenated)."""
    subjects = [CourseCertSubject(SALES_EGOIST_SUBJECT, "Sales Egoist", "sales-egoist")]
    for pid in sorted(product_ids):
        subjects.append(
            CourseCertSubject(
                product_subject_key(pid), f"{pid} product", _product_backing_slug(pid)
            )
        )
    return subjects


def course_cert_status(*, course_complete: bool, has_signoff: bool) -> CourseCertificationStatus:
    """Fold completion + sign-off into a status. A sign-off is only recorded once the course is
    complete (the repository gates it), so `has_signoff` implies certified."""
    if has_signoff:
        return CourseCertificationStatus.CERTIFIED
    if course_complete:
        return CourseCertificationStatus.IN_PROGRESS
    return CourseCertificationStatus.NOT_STARTED


def signoff_blockers(
    *, course_complete: bool, signer_is_senior: bool, signer_is_learner: bool
) -> list[str]:
    """Why a course-cert sign-off may NOT be recorded. Empty ⟹ the pairing is valid. A cert is never
    self-signed (that would be self-report, not pairing) and only a senior may sign it."""
    blockers: list[str] = []
    if not course_complete:
        blockers.append("The learner has not completed the course.")
    if signer_is_learner:
        blockers.append("A certification cannot be self-signed — pairing needs a different senior.")
    if not signer_is_senior:
        blockers.append("Only a Certified Lead (or an admin) may sign off a course certification.")
    return blockers
