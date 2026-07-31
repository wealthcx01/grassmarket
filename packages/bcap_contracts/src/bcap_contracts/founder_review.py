"""Founder review gate contracts (GRS-0188, ADR-0041).

The Bruntsfield Advisory Network is one founder and a small group of advisors. Peer rating,
Rating Committee sign-off and calibration sessions were built for a scale the network has not
reached, and the founder has asked for the simple thing instead: every client-facing draft comes
to them, and they sign what goes out.

A `FounderApproval` records that the founder approved **one specific version** of an assessment
document. It carries the sha256 of the document as it stood at approval time. The gate matches on
the *current* document hash, so an approval for a superseded version simply stops matching and the
record is back in the queue. That is the whole mechanism: no status column, no state machine, and
nothing to un-approve. Approvals are append-only, like every other record of a decision here.

The hash is computed server-side from the stored document and is never accepted from a caller.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field

from bcap_contracts.base import OwnedResource


class FounderApproval(OwnedResource):
    """The founder's sign-off on one version of one assessment document.

    `owner_consultant_id` is the advisor who owns the assessment, not the founder. Scoping stays
    the advisor's: an approval is visible to the advisor whose work it clears, and to the founder
    through the review queue. `approved_by_consultant_id` is who signed.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    assessment_id: UUID = Field(description="The assessment this approval clears.")
    document_hash: str = Field(
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description=(
            "Lowercase sha256 hex of the assessment document as stored at the moment of "
            "approval. Server-computed. An approval clears the gate only while this still "
            "equals the document's current hash, so any edit re-opens review."
        ),
    )
    approved_by_consultant_id: UUID = Field(
        description="The consultant who signed. Always the configured founder reviewer."
    )
    approved_at: datetime = Field(description="When the approval was recorded (UTC).")


class FounderReviewQueueEntry(OwnedResource):
    """One row of the founder's review queue: an assessment awaiting sign-off, with enough context
    to open it. Computed, never stored — the queue is derived from requests and approvals."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    assessment_id: UUID = Field(description="The assessment awaiting review.")
    # Set when this row is a CLIENT REPORT awaiting sign-off rather than an assessment (GRS-0245).
    # One queue rather than two, because the founder's question is the same either way — "what is
    # waiting on me" — and a second list is a second thing to forget to open.
    deliverable_id: UUID | None = Field(
        default=None,
        description="The deliverable whose client report awaits sign-off; null for an assessment.",
    )
    changed_sections: tuple[str, ...] = Field(
        default=(),
        description=(
            "For a re-review of a client report: which of the six sections differ from the version "
            "the founder last approved. Empty on a first review, where everything is new."
        ),
    )
    subject: str = Field(description="The company being assessed.")
    advisor_name: str = Field(description="The advisor who submitted it.")
    advisor_email: str = Field(description="How to reach them about it.")
    requested_at: datetime = Field(description="When review was requested (UTC).")
    document_hash: str = Field(
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="Current hash of the document to be approved.",
    )
    previously_approved: bool = Field(
        description=(
            "True when this assessment carries an approval at an older hash, meaning it was "
            "signed off and then edited. The founder is re-reviewing, not reviewing."
        )
    )
