"""Rating Committee contracts (GRS-0021, Methodology §8) — high-stakes ratings need peer sign-off.

The methodology disciplines judgment by peer challenge, not formula: **any power rated Established
or above, any triad rating above None, and any module whose rating gate is Frontier** requires
Rating Committee approval with recorded rationale and dissent. These are the ratings a client would
weight most, so a single assessor never gets the last word on them.

A `CommitteeItem` is a *computed* requirement (derived from the scored result — see
`grassmarket.atlas.committee`); a `CommitteeDecision` is the *stored* record of the committee's call
on one item, at the specific rating it reviewed. A decision only clears the finalise / client-pack
gate while its `rating` still matches the current score — re-rating a high-stakes item re-opens it.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from bcap_contracts.base import OwnedResource


class CommitteeItemType(StrEnum):
    """The three kinds of high-stakes rating that require committee sign-off (Methodology §8)."""

    POWER = "power"  # a Strategic Power rated Established or above
    TRIAD = "triad"  # a Platform Power triad dimension rated above None
    MODULE = "module"  # an infrastructure module whose rating gate is Frontier


class CommitteeDecisionStatus(StrEnum):
    """A committee call. The absence of a decision is 'pending' — never stored, always computed."""

    APPROVED = "approved"
    REJECTED = "rejected"


class CommitteeItem(BaseModel):
    """A computed sign-off requirement: which item, at which rating, and why it is high-stakes.

    Not persisted — derived from the scored `AtlasResult`. `item_key` is stable (a power/module
    registry key, or a `TriadDimension` value); `rating` is the current headline rating that
    triggered the requirement, so a decision is only valid while it still matches."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    item_type: CommitteeItemType
    item_key: str
    rating: str = Field(min_length=1, description="The high-stakes rating requiring sign-off.")
    label: str = Field(min_length=1, description="Human-readable name of the item.")
    reason: str = Field(min_length=1, description="Why this item needs committee approval.")


class CommitteeDecision(OwnedResource):
    """The committee's recorded call on one high-stakes item, at the rating it reviewed.

    `owner_consultant_id` is the assessment's owner (the record is scoped to the assessment);
    `decided_by_consultant_id` is the committee member who made the call — never the owner, so a
    consultant cannot sign off their own high-stakes ratings (peer challenge, Methodology §8)."""

    model_config = ConfigDict(extra="forbid")

    assessment_id: UUID
    item_type: CommitteeItemType
    item_key: str
    rating: str = Field(min_length=1, description="The rating the committee reviewed.")
    status: CommitteeDecisionStatus
    rationale: str = Field(min_length=1, description="Recorded rationale for the call (§8).")
    dissent_note: str | None = Field(
        default=None, description="Recorded dissent on a split decision (§8)."
    )
    decided_by_consultant_id: UUID
    decided_at: datetime


class CommitteeQueueEntry(BaseModel):
    """One row of the committee queue for an assessment: a required item and the current decision on
    it (if any). `decision is None` ⟹ pending; a decision whose `rating` differs from `item.rating`
    is stale (the item was re-rated after the call) and does not clear the gate."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    item: CommitteeItem
    decision: CommitteeDecision | None = None
