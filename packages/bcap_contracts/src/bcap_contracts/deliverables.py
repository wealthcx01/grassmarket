"""Deliverables (PRD §5) — with the ActiveGraph approval gate as a first-class field.

'AI proposes, humans approve' is a runtime guarantee (CLAUDE.md non-negotiable #8): a
deliverable whose draft is AI-generated cannot be `APPROVED` without a recorded human approver.
The engine that enforces the state machine is a later loop; the contract makes the states and
the approver field explicit now so nothing AI-generated can silently reach a client.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from bcap_contracts.base import OwnedResource


class DeliverableType(StrEnum):
    EXECUTIVE_SUMMARY = "executive_summary"
    PLATFORM_POWER_REPORT = "platform_power_report"
    INFRASTRUCTURE_HEATMAP = "infrastructure_heatmap"
    MODERNISATION_ROADMAP = "modernisation_roadmap"
    TECHNICAL_APPENDIX = "technical_appendix"
    WORKSHOP_OUTPUT = "workshop_output"
    SCORE_EVOLUTION = "score_evolution"


class ApprovalStatus(StrEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


class Deliverable(OwnedResource):
    model_config = ConfigDict(extra="forbid")

    engagement_id: UUID
    type: DeliverableType
    title: str = Field(min_length=1)
    ai_generated: bool = False
    approval_status: ApprovalStatus = ApprovalStatus.DRAFT
    approved_by_consultant_id: UUID | None = None

    @model_validator(mode="after")
    def _approved_requires_human(self) -> Deliverable:
        if (
            self.approval_status is ApprovalStatus.APPROVED
            and self.approved_by_consultant_id is None
        ):
            raise ValueError(
                "An APPROVED deliverable requires approved_by_consultant_id — AI-generated "
                "content never reaches a client without consultant sign-off (non-negotiable #8)."
            )
        return self
