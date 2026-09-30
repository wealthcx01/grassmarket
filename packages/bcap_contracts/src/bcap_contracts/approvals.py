"""The approval event log: proposed, granted, executed. One shape, three systems.

HC-005 and HC-042, plan D7. Deliberately the SAME SHAPE as the Foundry Studio's own event log, so
the two are one type rather than two that happen to look alike. The Foundry Studio writes these to
git refs today and is moving to a real event store (FB-171); Holy Corner starts on the event store.
Both read the same events.

**This is the one gate that is never bypassed.** Nothing external - an invoice sent, an email, a
reminder, a payment recorded, another studio told a client paid - happens without a person saying
yes, and the yes is a record nobody can forge or lose.

Five properties are built into the shape rather than left to the code that writes it:

1. **Append only.** There is no "update an approval" event, because there is no such thing. A
   decision that changed is a new event; the old one still happened.
2. **Ordered by `seq`, never by clock.** Two events a millisecond apart on two machines have an
   unarguable order by integer and an arguable one by timestamp. `at` is for a reader.
3. **Only a human grants.** `actor.kind` is checked at write time. An agent that could grant its own
   proposal is the entire gate, absent. CLAUDE.md #5: AI proposes, a person approves.
4. **Every event carries an attestation** - an HMAC over its canonical form. An event that does not
   verify is REFUSED AND COUNTED, not skipped quietly: an audit trail the audited party can write is
   worse than no audit trail, and one that silently drops what it cannot read is worse still.
5. **A grant is bound to a content hash.** The thing approved is the thing executed. A proposal
   whose payload changed after the grant cannot execute, so "approve this £500 payment" cannot
   become £5,000 between the yes and the doing.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ApprovalEventType(StrEnum):
    """The whole lifecycle. A proposal ends granted-then-executed, rejected, or failed."""

    PROPOSED = "approval.proposed"
    GRANTED = "approval.granted"
    REJECTED = "approval.rejected"
    EXECUTING = "action.executing"
    EXECUTED = "action.executed"
    FAILED = "action.failed"


class ActorKind(StrEnum):
    """Who did this.

    The distinction is load-bearing and is the reason this is an enum rather than a string. Only a
    `HUMAN` may grant. An `AGENT` proposes; an `EXECUTOR` is the one code path that performs an
    external action, and it acts only on a grant it has verified.
    """

    HUMAN = "human"
    AGENT = "agent"
    EXECUTOR = "executor"


class Actor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: ActorKind
    id: str = Field(
        min_length=1,
        description="Who, precisely enough to ask them about it later: a person's email, an "
        "agent's name, the executor's identifier.",
    )


class ApprovalEvent(BaseModel):
    """One event in the log. Immutable by construction: `frozen=True`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    v: int = Field(default=1, ge=1, description="Shape version, so a reader can tell old from new.")
    seq: int = Field(
        ge=1,
        description="Monotonic within a scope. THE ORDER OF THE LOG. Never sort these by "
        "`at`: two events a millisecond apart have an unarguable order by integer and an "
        "arguable one by clock.",
    )
    scope: str = Field(
        min_length=1,
        description="Which log this belongs to. The Foundry Studio scopes by venture; Holy Corner "
        "scopes by the subject the approval is about.",
    )
    id: str = Field(
        min_length=1, description="The proposal this event concerns. Stable across its life."
    )
    type: ApprovalEventType
    at: datetime = Field(description="When, for a reader. Not the ordering (see `seq`).")
    actor: Actor
    data: dict[str, object] = Field(
        default_factory=dict, description="What this event is about, in the kind's own terms."
    )
    content_hash: str | None = Field(
        default=None,
        description="A hash of the proposal's payload. Carried on the proposal and on the grant, "
        "so an executor can prove the thing approved is the thing it is about to do.",
    )
    attestation: str | None = Field(
        default=None,
        description="HMAC over the event's canonical form. Absent only on an event that has not "
        "been signed yet; a stored event without one does not verify and is refused.",
    )

    @model_validator(mode="after")
    def _only_a_human_grants_or_rejects(self) -> ApprovalEvent:
        deciding = {ApprovalEventType.GRANTED, ApprovalEventType.REJECTED}
        if self.type in deciding and self.actor.kind is not ActorKind.HUMAN:
            raise ValueError(
                f"{self.type.value} was recorded by an actor of kind {self.actor.kind.value!r}. "
                "Only a human may decide. An agent that can grant its own proposal is the gate "
                "removed, and a self-declared actor is not authorisation (CLAUDE.md #5)."
            )
        return self

    @model_validator(mode="after")
    def _only_the_executor_executes(self) -> ApprovalEvent:
        doing = {
            ApprovalEventType.EXECUTING,
            ApprovalEventType.EXECUTED,
            ApprovalEventType.FAILED,
        }
        if self.type in doing and self.actor.kind is not ActorKind.EXECUTOR:
            raise ValueError(
                f"{self.type.value} was recorded by an actor of kind {self.actor.kind.value!r}. "
                "Only the executor performs an external action, and only against a grant it has "
                "verified."
            )
        return self

    @model_validator(mode="after")
    def _a_grant_names_what_it_approved(self) -> ApprovalEvent:
        if self.type is ApprovalEventType.GRANTED and not self.content_hash:
            raise ValueError(
                "a grant must carry the content hash of what it approved. Without it there is "
                "nothing stopping the payload changing between the yes and the doing, which is "
                "the difference between approving a payment and approving an amount."
            )
        return self


class ProposalStatus(StrEnum):
    """The projection of a log, for a screen. Derived, never stored as the truth."""

    PROPOSED = "proposed"
    GRANTED = "granted"
    REJECTED = "rejected"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"
    # An event that did not verify. Surfaced and counted, never skipped: a trail that quietly drops
    # what it cannot read is worse than one that has a hole in it, because it looks complete.
    UNVERIFIED = "unverified"


class Proposal(BaseModel):
    """What a screen shows: one proposal, its state, and who decided it."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    kind: str = Field(
        min_length=1,
        description="What is being proposed, e.g. 'invoice.send' or 'payment.record'. The executor "
        "registry keys off this.",
    )
    subject: str = Field(min_length=1, description="What it is about, e.g. an invoice number.")
    status: ProposalStatus
    proposed_at: datetime
    proposed_by: Actor
    decided_at: datetime | None = None
    decided_by: Actor | None = None
    executed_at: datetime | None = None
    content_hash: str | None = None
    refused_events: int = Field(
        default=0,
        ge=0,
        description="How many events in this proposal's log failed to verify. Shown, not hidden.",
    )

    @model_validator(mode="after")
    def _a_decision_has_a_decider(self) -> Proposal:
        decided = {
            ProposalStatus.GRANTED,
            ProposalStatus.REJECTED,
            ProposalStatus.EXECUTING,
            ProposalStatus.EXECUTED,
            ProposalStatus.FAILED,
        }
        if self.status in decided and self.decided_by is None:
            raise ValueError(
                f"a proposal in status {self.status.value!r} was decided, so decided_by is "
                "required. A decision with nobody attached is the question this log answers."
            )
        return self
