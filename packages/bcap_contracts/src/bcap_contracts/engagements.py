"""Engagements and workshops (PRD §4) — the delivery layer above a qualified prospect."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from bcap_contracts.base import OwnedResource


class EngagementStatus(StrEnum):
    SCOPED = "scoped"
    CONTRACTED = "contracted"
    ACTIVE = "active"
    DELIVERED = "delivered"
    CLOSED = "closed"


class DeliverableStatus(StrEnum):
    """Progress of one deliverable slot. Deliverable *content* is Loop 4 (the builder); this is the
    forward-compatible progress shell only — a closed status set, no fabricated content."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DRAFTED = "drafted"
    DELIVERED = "delivered"


class DeliverableSlot(BaseModel):
    """A placeholder for one deliverable's progress. The Loop 4 builder fills the content; here we
    carry only a key + a status so the engagement can track progress before the builder exists."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1, description="Deliverable identifier the Loop 4 builder owns.")
    label: str | None = None
    status: DeliverableStatus = DeliverableStatus.NOT_STARTED


class CommsChannel(StrEnum):
    NOTE = "note"
    EMAIL = "email"
    CALL = "call"
    MEETING = "meeting"


class CommsLogEntry(BaseModel):
    """One timestamped communication-log entry. Append-only in practice (the repository never
    updates one); ordering is by ``at``."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    at: datetime
    channel: CommsChannel
    author_consultant_id: UUID
    body: str = Field(min_length=1)


class Engagement(OwnedResource):
    """A contracted prospect's delivery record: which assessment(s) it draws on, a deliverables
    progress shell (Loop 4 fills content), and a communication log (PRD §4)."""

    model_config = ConfigDict(extra="forbid")

    prospect_id: UUID
    title: str = Field(min_length=1)
    status: EngagementStatus = EngagementStatus.SCOPED
    started_on: date | None = None
    assessment_ids: tuple[UUID, ...] = Field(
        default=(), description="Finalised assessments this engagement draws on (GRS-0009)."
    )
    deliverables: tuple[DeliverableSlot, ...] = ()
    comms_log: tuple[CommsLogEntry, ...] = ()


class WorkshopState(StrEnum):
    """A workshop is scheduled, then delivered (PRD §4). Recovery-fee attribution keys off the
    delivered date + the config window; the window itself is NOT a per-workshop field (it is
    configuration — GRS-0012)."""

    SCHEDULED = "scheduled"
    DELIVERED = "delivered"


class Workshop(OwnedResource):
    """A workshop in a consultant's pipeline, linked to a prospect (PRD §4)."""

    model_config = ConfigDict(extra="forbid")

    prospect_id: UUID
    state: WorkshopState = WorkshopState.SCHEDULED
    scheduled_for: date | None = None
    delivered_on: date | None = None
    pre_workshop_brief: str | None = None
    workshop_output: str | None = None
