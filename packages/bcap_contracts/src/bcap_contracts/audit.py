"""Append-only audit log + GDPR export bundle (GRS-0032, PRD §2; Viewforth data-protection).

Every security-relevant action writes an immutable `AuditEvent` (who did what to which resource,
when) — auth, scoring finalisation, deliverable generation/download, committee decisions,
certification overrides, commission recording. The log is append-only — events are inserted, never
updated or deleted. `PersonalDataExport` is the GDPR subject-access bundle — every record the
platform holds about one person, gathered for export.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from bcap_contracts.base import OwnedResource


class AuditEventType(StrEnum):
    """The security-relevant action classes the audit log records (PRD §2)."""

    AUTH_LOGIN = "auth_login"
    AUTH_PASSWORD_CHANGED = "auth_password_changed"
    AUTH_ACCOUNT_AUTOPROVISIONED = "auth_account_autoprovisioned"
    ASSESSMENT_FINALISED = "assessment_finalised"
    # ADR-0047 (2026-07-29 amendment): a production record was deleted by founder decision. The
    # one deletion here that could ever have destroyed real work, so it leaves a permanent trace.
    ASSESSMENT_DELETED = "assessment_deleted"
    DELIVERABLE_GENERATED = "deliverable_generated"
    DELIVERABLE_DOWNLOADED = "deliverable_downloaded"
    COMMITTEE_DECISION = "committee_decision"
    FOUNDER_APPROVAL = "founder_approval"  # ADR-0041: the founder signed off a document version
    CERTIFICATION_OVERRIDE = "certification_override"
    COMMISSION_RECORDED = "commission_recorded"
    # GRS-0208: an admin opened or closed a session scoped to another consultant. Both identities
    # are on the event — the admin as actor, the subject as the resource — because an act-as with
    # no trace is impersonation, and the difference between the two is exactly this record.
    ACT_AS_STARTED = "act_as_started"
    ACT_AS_ENDED = "act_as_ended"
    GDPR_EXPORT = "gdpr_export"
    GDPR_DELETION = "gdpr_deletion"


class AuditEvent(OwnedResource):
    """One append-only audit record. `owner_consultant_id` is the ACTOR (who did it); the target is
    `resource_type` + `resource_id`. Never mutated after write."""

    model_config = ConfigDict(extra="forbid")

    event_type: AuditEventType
    resource_type: str | None = None
    resource_id: UUID | None = None
    detail: str | None = Field(default=None, description="A short human-readable note, no secrets.")
    at: datetime


class PersonalDataExport(BaseModel):
    """A GDPR subject-access bundle: every record the platform holds about one person, keyed by
    resource type. Values are plain dicts of each row's columns (ids + timestamps included)."""

    model_config = ConfigDict(extra="forbid")

    subject_consultant_id: UUID
    generated_at: datetime
    records: dict[str, list[dict[str, Any]]]
