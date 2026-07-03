"""Shared base models for API resources — the shape the Holy Corner API will expose.

`OwnedResource` carries the ``owner_consultant_id`` that the Grassmarket repository layer uses
to enforce absolute data scoping (CLAUDE.md non-negotiable #9). Scoping is enforced in ONE
place — the repository — but the ownership field lives on the contract so the seam is explicit.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ResourceBase(BaseModel):
    """Common identity + audit fields for every persisted resource."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    created_at: datetime
    updated_at: datetime


class OwnedResource(ResourceBase):
    """A resource scoped to a single consultant. The repository never returns one of these to a
    principal who does not own it (unless an explicit governance role widens visibility)."""

    owner_consultant_id: UUID = Field(
        description="The consultant who owns this resource. Data scoping is by this field, "
        "enforced in the repository layer and tested from day one."
    )
