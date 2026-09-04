"""The one needs-you queue (GRS-0253, Advisor Studio Backend Request R1, gap G5).

Everything waiting on an advisor is **one idea to them and several endpoints to us**. Four surfaces
— the desk, the needs-you screen, the rail badge, the pocket — each composed the same merge, so the
badge could disagree with the page it linked to. One read model, one order, one count.

**Nothing here is stored.** The queue is derived on every read from the records it describes, so it
cannot go stale and there is no second copy of the truth to reconcile.

**Dormant sources are named, not hidden.** Peer rating and committee sign-off are retired under
ADR-0041; the founder signs what goes out instead. A queue that silently omitted them would look
identical to a queue that had nothing waiting, and the design contract is explicit that anything
unbuilt says so in words. So the queue reports what it cannot currently see, and why.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class NeedsYouKind(StrEnum):
    """What the advisor has to *do*, which is the only grouping they think in."""

    #: Cleared to go out and not yet gone. Nothing covered this before GRS-0253.
    SEND = "send"
    #: A module assigned to the caller to rate. Dormant under ADR-0041.
    RATE = "rate"
    #: Something awaiting the caller's sign-off.
    APPROVE = "approve"


class NeedsYouTarget(StrEnum):
    """What the item points at, so the UI can route without parsing the reason."""

    ASSESSMENT = "assessment"
    CLIENT_REPORT = "client_report"
    MODULE_RATING = "module_rating"


class NeedsYouItem(BaseModel):
    """One thing waiting on the caller."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: NeedsYouKind
    target: NeedsYouTarget
    target_id: UUID = Field(description="The record to open — an assessment or a deliverable.")
    subject: str = Field(min_length=1, description="The company, so the row reads as a thing.")
    #: The clock the UI shows as a waited-time. **Not** `created_at`: the record may have existed
    #: for weeks before it started waiting on anybody, and a waited-time measured from creation
    #: would overstate every row on the screen.
    became_actionable_at: datetime = Field(
        description="When this started waiting on the caller (UTC)."
    )
    reason: str = Field(
        min_length=1,
        description="One line in the product's voice: what is waiting, and what happens next.",
    )


class DormantSource(BaseModel):
    """A kind of work this queue cannot currently show, and why.

    Carried rather than omitted. An empty queue and a queue whose sources are switched off look
    the same on screen, and only one of them means "you are up to date".
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: NeedsYouKind
    reason: str = Field(min_length=1, description="Why it is dormant, in words, with the ADR.")


class NeedsYouQueue(BaseModel):
    """Everything waiting on one advisor, oldest first."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    generated_at: datetime
    #: Oldest first. The longest-waiting thing is the one most likely to be forgotten, so it is the
    #: one that reads first.
    items: tuple[NeedsYouItem, ...] = ()
    dormant: tuple[DormantSource, ...] = ()

    @property
    def count(self) -> int:
        """What the rail badge shows. Defined here so the badge and the page cannot disagree."""
        return len(self.items)
