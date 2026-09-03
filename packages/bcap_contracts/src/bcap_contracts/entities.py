"""Pipeline entities — prospects/clients, entity-shaped for later Holy Corner sync (PRD §4)."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
    #: The one thing that has to happen next, and when (GRS-0249 scope 4). A deal with no dated
    #: next action is drifting, which is the judgement the Sales Ops course teaches and the
    #: pipeline had no field to record. Free text on purpose: "send the revised fee schedule" is
    #: the useful form, not an enum.
    next_action: str | None = Field(
        default=None, max_length=280, description="The single next thing to do for this prospect."
    )
    #: Nullable independently of `next_action`. An action with no date is honest — the advisor
    #: knows what to do and not yet when — and inventing a date to fill the column would be
    #: the fabrication non-negotiable #3 exists to prevent.
    next_action_on: date | None = Field(
        default=None, description="When the next action is due, if the advisor set a date."
    )


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


class CompanyEntity(BaseModel):
    """A canonical company an assessment subject can resolve to (GRS-0100, ADR-0033). Reference
    data, not owner-scoped: `entity_id` is the durable key an assessment points at, `name` is the
    canonical display name, and `aliases` are the variants that should collapse to one entity
    ("Revolut" / "Revolut Ltd"). Served by the injectable EntityRegistry (a seeded stub today, a
    real registry later behind the same port)."""

    model_config = ConfigDict(extra="forbid")

    entity_id: str = Field(min_length=1, description="Stable canonical id, e.g. a registry slug.")
    name: str = Field(min_length=1)
    aliases: tuple[str, ...] = ()
    domain: str | None = None
    segment: str | None = Field(
        default=None, description="Coarse sector hint, e.g. 'Neobank' or 'Broker'."
    )


class RegistryTarget(BaseModel):
    """An institution in the shared GTM target registry (GRS-0193, ADR-0045). Network-shared
    reference data, deliberately NOT owner-scoped: every consultant searches the same imported
    universe. `CompanyEntity` is derived from this by a pure adapter, so the `EntityRegistry`
    search port is unchanged and only its corpus grows.

    `source` records which dataset the row came from, and `imported_on` when, so a row's provenance
    survives re-import. Both are required: an unattributed target is not importable (fail loud, #3).
    """

    model_config = ConfigDict(extra="forbid")

    target_id: str = Field(min_length=1, description="Stable slug, unique across all sources.")
    name: str = Field(min_length=1)
    aliases: tuple[str, ...] = ()
    domain: str | None = None
    segment: str | None = Field(
        default=None, description="Coarse sector hint, e.g. 'Bank' or 'Exchange supplier'."
    )
    country: str | None = None
    ric: str | None = Field(
        default=None,
        description="An LSEG RIC this institution was seen against, where known (GRS-0194).",
    )
    ctb_id: int | None = Field(
        default=None,
        description="LSEG/I-B-E-S contributor id — the per-institution grouping key for analyst "
        "rosters. Null for targets from non-LSEG sources.",
    )
    source: str = Field(min_length=1, description="Dataset provenance token, e.g. 'lseg-roster'.")
    imported_on: date


class RegistryContact(BaseModel):
    """A named person at a `RegistryTarget` (GRS-0193, ADR-0045). Network-shared: any authenticated
    consultant may read the shared universe, which is the one deliberate exception to owner-scoping
    (#9) and is test-enforced so it cannot leak into owner-scoped resources.

    This is personal data. Rows live in the database only, never in a committed fixture, and they
    are carried by the SAR export and erasure paths.
    """

    model_config = ConfigDict(extra="forbid")

    contact_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    email: str | None = None
    phone: str | None = None
    job_role: str | None = None
    linkedin: str | None = None
    verified: bool = Field(
        default=False,
        description="Whether a human confirmed this person and role against a named source. An "
        "inferred or unaudited row stays False and renders flagged, never as verified.",
    )
    source: str = Field(min_length=1)
    imported_on: date
