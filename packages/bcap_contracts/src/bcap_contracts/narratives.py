"""AI first-draft narratives (GRS-0017, PRD §5) — 'AI proposes, humans approve' as typed state.

An `AINarrative` is one AI-drafted section (interpretation / commentary / recommendation) bound to a
deliverable and its finalised scoring run. It carries the proposal text, a versioned attribution to
the drafter + prompt template that produced it, and — once a human signs off — the approval trail:
who approved, when, the final (possibly consultant-edited) text, and a summary of what changed.

The state machine is the runtime guarantee of non-negotiable #8: a narrative is `APPROVED` only with
a recorded human approver AND final text; `PROPOSED`/`REJECTED` carry neither. The client-usable
gate (GRS-0015/GRS-0017) refuses any client-facing pack containing a not-`APPROVED` narrative.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import ConfigDict, Field, model_validator

from bcap_contracts.base import OwnedResource
from bcap_contracts.common import ConsultantTier


class NarrativeSection(StrEnum):
    """The AI-drafted prose sections of a deliverable (PRD §5)."""

    INTERPRETATION = "interpretation"
    COMMENTARY = "commentary"
    RECOMMENDATION = "recommendation"


class NarrativeStatus(StrEnum):
    """Proposal lifecycle. AI output starts PROPOSED and reaches a client only once APPROVED."""

    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"


class AINarrative(OwnedResource):
    """One AI-drafted, human-gated deliverable section. Bound to a deliverable + scoring run so the
    proposal is always attributable to the run it interprets and the drafter that wrote it."""

    model_config = ConfigDict(extra="forbid")

    deliverable_id: UUID
    scoring_run_id: UUID
    section: NarrativeSection
    status: NarrativeStatus = NarrativeStatus.PROPOSED

    proposed_text: str = Field(
        min_length=1, description="The AI's first draft — never client-bound."
    )
    drafter_version: str = Field(min_length=1, description="Which drafter produced the proposal.")
    prompt_template_version: str = Field(
        min_length=1, description="Which template version was used."
    )
    author_tier: ConsultantTier = Field(
        description="Tier of the consultant who commissioned the draft — drives the seniority gate."
    )

    # Approval trail (all None until a human signs off).
    final_text: str | None = Field(
        default=None, description="The approved text (may differ from the proposal after edits)."
    )
    approved_by_consultant_id: UUID | None = None
    approved_at: datetime | None = None
    edit_summary: str | None = Field(
        default=None, description="Human-readable diff of consultant edits from proposal to final."
    )

    @model_validator(mode="after")
    def _approval_trail_is_consistent(self) -> AINarrative:
        approved = self.status is NarrativeStatus.APPROVED
        has_approver = self.approved_by_consultant_id is not None
        if approved and not (has_approver and self.approved_at and self.final_text):
            raise ValueError(
                "An APPROVED narrative requires approved_by_consultant_id, approved_at and "
                "final_text — AI content never reaches a client without human sign-off (#8)."
            )
        if not approved and (has_approver or self.approved_at or self.final_text):
            raise ValueError(
                "A non-APPROVED narrative must not carry an approval trail "
                "(approver/approved_at/final_text)."
            )
        return self
