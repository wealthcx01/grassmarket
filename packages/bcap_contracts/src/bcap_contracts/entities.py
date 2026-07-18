"""Pipeline entities — prospects/clients, entity-shaped for later Holy Corner sync (PRD §4)."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import ConfigDict, Field

from bcap_contracts.base import OwnedResource


class PipelineStage(StrEnum):
    """Kanban stages (PRD §4). Ordered; time-in-stage flags key off the transitions."""

    PROSPECT = "prospect"
    WORKSHOP_SCHEDULED = "workshop_scheduled"
    WORKSHOP_DELIVERED = "workshop_delivered"
    QUALIFIED = "qualified"
    SCOPED = "scoped"
    CONTRACTED = "contracted"
    ACTIVE = "active"
    DELIVERED = "delivered"
    CLOSED = "closed"
    NURTURE = "nurture"


class Prospect(OwnedResource):
    """A prospect/client in a consultant's pipeline. Scoped to its owner (repository-enforced).

    'Entity-shaped' means the identifying fields mirror the future Holy Corner entity resource,
    so a later sync maps cleanly rather than reshaping the record.
    """

    model_config = ConfigDict(extra="forbid")

    company_name: str = Field(min_length=1)
    stage: PipelineStage = PipelineStage.PROSPECT
    stage_entered_at: datetime = Field(
        description="When the prospect entered its current stage — the basis for time-in-stage "
        "flags. Set on creation and updated on every (validated) stage transition."
    )
    sector: str | None = None
    website: str | None = None
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    notes: str | None = None


class Contact(OwnedResource):
    """A person at a prospect's company (GRS-0111) — a first-class, owner-scoped entity so a deal
    can carry its whole buying unit (many contacts per prospect), not just one inline name/email.
    One contact may be flagged `is_primary`; the prospect's `primary_contact_*` fields mirror it for
    the win-probability scorer and back-compat."""

    model_config = ConfigDict(extra="forbid")

    prospect_id: UUID
    name: str = Field(min_length=1)
    email: str | None = None
    phone: str | None = None
    title: str | None = Field(default=None, description="Role / job title, e.g. 'Head of Trading'.")
    is_primary: bool = False
