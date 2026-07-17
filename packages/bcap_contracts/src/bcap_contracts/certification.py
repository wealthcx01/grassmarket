"""Certification-ladder contracts (GRS-0023, Methodology §9) — capability, enforced, not a badge.

The CMMI-appraiser ladder Trained → Shadow → Observed Lead → Certified Lead (the `AssessorLevel`
enum) is advanced only on recorded EVIDENCE: coursework + a passed rubric exam, two shadow
assessments, an observed lead (led one under review), and finally a sign-off by an existing
Certified Lead. A `CertificationRecord` accumulates that evidence; a `CertificationEvent` is the
audit of every credit, promotion, and admin override (nothing is bypassed silently).

High-stakes ratings (a Frontier module, a Wide power) require a Certified Lead on the assessment —
a runtime refusal at finalisation, overridable only by an admin with a recorded reason.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from bcap_contracts.base import OwnedResource
from bcap_contracts.common import AssessorLevel

# The rubric-exam pass mark (Methodology §9). A coefficient of the ladder, kept in one place.
EXAM_PASS_MARK = 0.7
# Shadow assessments required to leave Trained (§9: "Shadow — participates in 2 assessments").
SHADOW_ASSESSMENTS_REQUIRED = 2


class CertificationEventKind(StrEnum):
    """Every entry in the append-only certification audit (Methodology §9)."""

    COURSEWORK_COMPLETED = "coursework_completed"
    EXAM_RECORDED = "exam_recorded"
    SHADOW_LOGGED = "shadow_logged"
    OBSERVED_LEAD_LOGGED = "observed_lead_logged"
    SIGNOFF_RECORDED = "signoff_recorded"
    PROMOTED = "promoted"
    OVERRIDE = "override"


class CertificationRecord(OwnedResource):
    """The accumulated ladder evidence for one advisor (`owner_consultant_id`). The advisor's LEVEL
    is on their consultant record (and JWT); this holds the evidence promotions are gated on."""

    model_config = ConfigDict(extra="forbid")

    level: AssessorLevel = AssessorLevel.TRAINED
    coursework_complete: bool = False
    exam_score: float | None = Field(default=None, ge=0.0, le=1.0)
    shadow_count: int = Field(default=0, ge=0)
    observed_lead_logged: bool = False
    observed_lead_signoff_by: UUID | None = Field(
        default=None, description="The Certified Lead who signed off the observed lead."
    )

    @property
    def exam_passed(self) -> bool:
        return self.exam_score is not None and self.exam_score >= EXAM_PASS_MARK


class CertificationEvent(OwnedResource):
    """One append-only certification audit record for an advisor (`owner_consultant_id`). Promotions
    carry from/to levels; an override carries the mandatory reason. Recorded by an admin/signer.

    `cert_subject` keeps this the SINGLE audit store for both tracks (GRS-0127): ``None`` is the
    assessor ladder; a value (e.g. ``sales_egoist`` or ``product:openbb``) is a course/product
    certification. No parallel cert store — a course cert is folded from these same events."""

    model_config = ConfigDict(extra="forbid")

    kind: CertificationEventKind
    detail: str = ""
    from_level: AssessorLevel | None = None
    to_level: AssessorLevel | None = None
    reason: str | None = Field(default=None, description="Mandatory for an OVERRIDE (§9).")
    cert_subject: str | None = Field(
        default=None, description="None = assessor ladder; else a course/product cert key."
    )
    recorded_by_consultant_id: UUID
    occurred_at: datetime

    @model_validator(mode="after")
    def _override_reason_is_mandatory(self) -> CertificationEvent:
        # Structural, not just a router check: an override without a recorded, non-blank reason is
        # a silent bypass, which §9 forbids (#3 fail-loud).
        if self.kind is CertificationEventKind.OVERRIDE and not (self.reason or "").strip():
            raise ValueError("An OVERRIDE certification event requires a non-blank reason (§9).")
        return self


class CourseCertificationStatus(StrEnum):
    """A course/product certification's state for one advisor (GRS-0127), folded from the events +
    course completion."""

    NOT_STARTED = "not_started"  # course not yet complete
    IN_PROGRESS = "in_progress"  # course complete, awaiting a senior sign-off (pairing)
    CERTIFIED = "certified"  # a senior signed off — certified


class CourseCertification(BaseModel):
    """One advisor's standing on a course/product certification (GRS-0127) — a read view folded from
    `CertificationEvent`s (`cert_subject == subject`) plus whether they have completed the backing
    course. Certification requires the course done AND a senior sign-off (not self) — the
    senior↔junior pairing, never self-report. A computed view, so no id/timestamps of its own."""

    model_config = ConfigDict(extra="forbid")

    owner_consultant_id: UUID
    subject: str = Field(min_length=1, description="The cert key, e.g. 'sales_egoist'.")
    title: str = Field(min_length=1)
    status: CourseCertificationStatus
    course_complete: bool
    signed_off_by_consultant_id: UUID | None = None
    certified_at: datetime | None = None
