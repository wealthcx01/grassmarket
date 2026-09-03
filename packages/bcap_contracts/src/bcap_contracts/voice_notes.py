"""Voice note → pipeline proposal (GRS-0249 scope 4).

The Path B pattern, one level down. Path B maps a transcript to a proposed **assessment**; this
maps one to a proposed **pipeline update** — the stage, the next action and its date, a line for
the communication log. The shape is deliberately the same, because the guarantee is the same:

**A voice note proposes. It never acts.** The proposed values live on the proposal, never on the
prospect, until an advisor confirms them. Non-negotiable #8 in full — *a voice note must never move
a prospect stage on its own.* Confirmation is the gate, and it is recorded.

Two things this adds to the Path B shape, because a spoken note is looser than a dictated
assessment:

1. **Every field is optional and its absence is meaningful.** A note that says nothing about the
   stage proposes no stage. `gaps` names what the extractor looked for and did not find, so the
   advisor can tell "it heard nothing about this" apart from "it heard nothing at all".
2. **The confirmed value is stored beside the proposed one.** When an advisor corrects a field, the
   record keeps both — what was suggested and what a human actually agreed to. That is the audit
   trail #8 is for, and a proposal that overwrote its own suggestion on confirmation could not
   answer the only question that matters afterwards: did a person change this, or did the machine?
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import ConfigDict, Field

from bcap_contracts.base import OwnedResource
from bcap_contracts.extraction import ExtractionConfidence


class PipelineField(StrEnum):
    """The fields a voice note may propose. Deliberately a closed set (ADR-0001): an extractor
    cannot invent a field name, and every one of these maps to an existing write path."""

    #: The prospect's pipeline stage. Applied through `update_prospect_stage`, so an illegal move
    #: is refused by the same lifecycle graph that refuses one made by hand.
    STAGE = "stage"
    #: What has to happen next, in the advisor's words.
    NEXT_ACTION = "next_action"
    #: When it is due. Separate from the action because an undated action is a real state.
    NEXT_ACTION_ON = "next_action_on"
    #: A line for the engagement's communication log.
    COMMS_NOTE = "comms_note"


class ProposalStatus(StrEnum):
    """A proposal is PROPOSED until a human does something about it. There is no expiry and no
    automatic application: an unanswered proposal stays unanswered, visibly."""

    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    #: The advisor read it and rejected it. Recorded rather than deleted — "the machine suggested
    #: this and a person said no" is worth keeping, and it is the only evidence that the gate is
    #: doing anything.
    DISCARDED = "discarded"


class ProposedField(OwnedResource):
    """One field a voice note proposed, what the advisor did with it, and where it came from."""

    model_config = ConfigDict(extra="forbid")

    proposal_id: UUID
    transcript_id: UUID
    field: PipelineField
    #: What the extractor suggested, as text. Text for every field so one table holds them all;
    #: the value is parsed and validated against its real type at confirmation, where a bad value
    #: is refused rather than coerced.
    proposed_value: str | None = Field(
        default=None, description="The extractor's suggestion, or null where it found nothing."
    )
    confidence: ExtractionConfidence
    span_start: int = Field(ge=0, description="Character offset of the supporting span.")
    span_end: int = Field(ge=0)
    accepted: bool = Field(
        default=False, description="True once the advisor confirmed this field specifically."
    )
    #: What the advisor actually confirmed. Equal to `proposed_value` when they accepted it as
    #: offered, different when they corrected it, null when they left it out. Kept beside the
    #: proposal rather than replacing it, so the record can always say who decided.
    confirmed_value: str | None = None


class VoiceNoteProposal(OwnedResource):
    """A gated pipeline proposal drawn from one voice note, against one prospect."""

    model_config = ConfigDict(extra="forbid")

    prospect_id: UUID
    transcript_id: UUID
    status: ProposalStatus = ProposalStatus.PROPOSED
    extractor_version: str = Field(min_length=1)
    gaps: tuple[str, ...] = Field(
        default=(),
        description="Fields the extractor looked for and did not find — stated, not left blank.",
    )
    fields: tuple[ProposedField, ...] = ()
    confirmed_at: datetime | None = None
    #: Set when the advisor discards the proposal, so the two terminal states are distinguishable
    #: without reading the status alone.
    discarded_at: datetime | None = None
