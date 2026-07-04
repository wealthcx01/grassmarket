"""Pipeline entities — prospects/clients, entity-shaped for later Holy Corner sync (PRD §4)."""

from __future__ import annotations

from enum import StrEnum

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
    sector: str | None = None
    primary_contact_name: str | None = None
    primary_contact_email: str | None = None
    notes: str | None = None
