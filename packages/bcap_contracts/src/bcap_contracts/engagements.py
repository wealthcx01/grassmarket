"""Engagements and workshops (PRD §4) — the delivery layer above a qualified prospect."""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import ConfigDict, Field

from bcap_contracts.base import OwnedResource


class EngagementStatus(StrEnum):
    SCOPED = "scoped"
    CONTRACTED = "contracted"
    ACTIVE = "active"
    DELIVERED = "delivered"
    CLOSED = "closed"


class Engagement(OwnedResource):
    model_config = ConfigDict(extra="forbid")

    prospect_id: UUID
    title: str = Field(min_length=1)
    status: EngagementStatus = EngagementStatus.SCOPED
    started_on: date | None = None


class Workshop(OwnedResource):
    """A workshop with its recovery-fee attribution window (PRD §4)."""

    model_config = ConfigDict(extra="forbid")

    prospect_id: UUID
    scheduled_for: date | None = None
    delivered_on: date | None = None
    pre_workshop_brief: str | None = None
    workshop_output: str | None = None
    recovery_fee_window_days: int = 365  # 12-month attribution window
