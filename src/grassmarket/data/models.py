"""SQLAlchemy ORM models — the Grassmarket storage shapes.

These are storage records, distinct from the `bcap_contracts` wire/API shapes. The password
hash lives ONLY here (`ConsultantORM.hashed_password`) — never on a contract that could be
serialised to a client. Loop 0 persists exactly what the auth flow and the scoping tests need:
consultants, invitations, and one owned pipeline resource (prospects).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from bcap_contracts.common import AssessorLevel, ConsultantTier, Role
from bcap_contracts.engagements import EngagementStatus, WorkshopState
from bcap_contracts.entities import PipelineStage
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from grassmarket.data.database import Base


def _now() -> datetime:
    return datetime.now(UTC)


class ConsultantORM(Base):
    __tablename__ = "consultants"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(String(32), default=Role.CONSULTANT, nullable=False)
    tier: Mapped[ConsultantTier] = mapped_column(
        String(32), default=ConsultantTier.VENTURE_ASSOCIATE, nullable=False
    )
    assessor_level: Mapped[AssessorLevel] = mapped_column(
        String(32), default=AssessorLevel.TRAINED, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class InvitationORM(Base):
    __tablename__ = "invitations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), index=True, nullable=False)
    # Only the HASH of the invite token is stored; the raw token is delivered out of band.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    role: Mapped[Role] = mapped_column(String(32), default=Role.CONSULTANT, nullable=False)
    tier: Mapped[ConsultantTier] = mapped_column(
        String(32), default=ConsultantTier.VENTURE_ASSOCIATE, nullable=False
    )
    invited_by_consultant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class ProspectORM(Base):
    __tablename__ = "prospects"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # THE scoping column: every read/list/write is filtered by this in the repository layer.
    owner_consultant_id: Mapped[UUID] = mapped_column(
        ForeignKey("consultants.id"), index=True, nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    stage: Mapped[PipelineStage] = mapped_column(
        String(32), default=PipelineStage.PROSPECT, nullable=False
    )
    # When the prospect entered its current stage — the basis for time-in-stage flags. Set on
    # creation and rewritten on every validated stage transition.
    stage_entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, nullable=False
    )
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True)
    primary_contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    primary_contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class WorkshopORM(Base):
    """A workshop owned by a consultant and linked to a prospect (GRS-0012, PRD §4). Scheduled,
    then delivered; the delivered date is the anchor for recovery-fee attribution."""

    __tablename__ = "workshops"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # THE scoping column — every read/list/write is filtered by this in the repository layer.
    owner_consultant_id: Mapped[UUID] = mapped_column(
        ForeignKey("consultants.id"), index=True, nullable=False
    )
    prospect_id: Mapped[UUID] = mapped_column(
        ForeignKey("prospects.id"), index=True, nullable=False
    )
    state: Mapped[WorkshopState] = mapped_column(
        String(16), default=WorkshopState.SCHEDULED, nullable=False
    )
    scheduled_for: Mapped[date | None] = mapped_column(Date, nullable=True)
    delivered_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    pre_workshop_brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    workshop_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class RecoveryFeeAttributionORM(Base):
    """An immutable, content-hashed recovery-fee attribution (GRS-0012). Append-only: rows are
    inserted, never updated. The £ fee is stored as integer minor units + currency (never a float)
    plus the assumption-register ref that justifies it; the content hash seals the record."""

    __tablename__ = "recovery_fee_attributions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # THE scoping column — every read/list is filtered by this in the repository layer.
    owner_consultant_id: Mapped[UUID] = mapped_column(
        ForeignKey("consultants.id"), index=True, nullable=False
    )
    # Unique: one recovery-fee attribution per delivered workshop (no double-attribution).
    workshop_id: Mapped[UUID] = mapped_column(
        ForeignKey("workshops.id"), unique=True, index=True, nullable=False
    )
    prospect_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)
    delivered_on: Mapped[date] = mapped_column(Date, nullable=False)
    contracted_on: Mapped[date] = mapped_column(Date, nullable=False)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    rate_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    fee_amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    fee_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    fee_assumption_ref: Mapped[str] = mapped_column(String(128), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class EngagementORM(Base):
    """A contracted prospect's delivery record (GRS-0013, PRD §4). The linked finalised assessments
    and the deliverables progress shell are stored as JSON (a partial/growing structure saves
    without a schema migration); the communication log is a separate append-only table."""

    __tablename__ = "engagements"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # THE scoping column — every read/list/write is filtered by this in the repository layer.
    owner_consultant_id: Mapped[UUID] = mapped_column(
        ForeignKey("consultants.id"), index=True, nullable=False
    )
    prospect_id: Mapped[UUID] = mapped_column(
        ForeignKey("prospects.id"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[EngagementStatus] = mapped_column(
        String(16), default=EngagementStatus.CONTRACTED, nullable=False
    )
    started_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    # JSON: a list of finalised assessment ids, and the deliverables progress shell (Loop 4 fills).
    assessment_ids_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    deliverables_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class CommsLogEntryORM(Base):
    """One append-only communication-log entry against an engagement (GRS-0013). Rows are inserted,
    never updated; ordering is by ``at`` then ``created_at``."""

    __tablename__ = "comms_log_entries"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # THE scoping column — every read/list is filtered by this in the repository layer.
    owner_consultant_id: Mapped[UUID] = mapped_column(
        ForeignKey("consultants.id"), index=True, nullable=False
    )
    engagement_id: Mapped[UUID] = mapped_column(
        ForeignKey("engagements.id"), index=True, nullable=False
    )
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    author_consultant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class DeliverableORM(Base):
    """A generated deliverable document tied to an engagement (GRS-0015). Metadata only — the .docx
    is regenerated deterministically from the finalised scoring run on download (no bytes stored).
    ``mode`` records the client-usable gate's decision; approval fields carry non-negotiable #8."""

    __tablename__ = "deliverables"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # THE scoping column — every read/list/write is filtered by this in the repository layer.
    owner_consultant_id: Mapped[UUID] = mapped_column(
        ForeignKey("consultants.id"), index=True, nullable=False
    )
    engagement_id: Mapped[UUID] = mapped_column(
        ForeignKey("engagements.id"), index=True, nullable=False
    )
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approval_status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    approved_by_consultant_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    mode: Mapped[str] = mapped_column(String(16), nullable=False)
    scoring_run_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    coefficient_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class AINarrativeORM(Base):
    """One AI-drafted, human-gated deliverable section (GRS-0017, non-negotiable #8). Bound to a
    deliverable + finalised scoring run; carries the proposal, its versioned attribution, and — once
    signed off — the approval trail (approver, timestamp, final text, edit diff). Scoped by
    ``owner_consultant_id`` like every owned resource."""

    __tablename__ = "ai_narratives"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # THE scoping column — every read/list/write is filtered by this in the repository layer.
    owner_consultant_id: Mapped[UUID] = mapped_column(
        ForeignKey("consultants.id"), index=True, nullable=False
    )
    deliverable_id: Mapped[UUID] = mapped_column(
        ForeignKey("deliverables.id"), index=True, nullable=False
    )
    scoring_run_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    section: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="proposed", nullable=False)
    proposed_text: Mapped[str] = mapped_column(Text, nullable=False)
    drafter_version: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_template_version: Mapped[str] = mapped_column(String(64), nullable=False)
    author_tier: Mapped[ConsultantTier] = mapped_column(String(32), nullable=False)
    final_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by_consultant_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    edit_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class CertificationRecordORM(Base):
    """The accumulated certification-ladder evidence for one advisor (GRS-0023, §9). One row per
    consultant (``owner_consultant_id`` unique). The advisor's LEVEL lives on ConsultantORM (and the
    JWT); this holds the evidence that promotions are gated on."""

    __tablename__ = "certification_records"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_consultant_id: Mapped[UUID] = mapped_column(
        ForeignKey("consultants.id"), unique=True, index=True, nullable=False
    )
    coursework_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exam_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    shadow_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    observed_lead_logged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    observed_lead_signoff_by: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class CertificationEventORM(Base):
    """One append-only certification audit record for an advisor (GRS-0023, §9). Every credit,
    promotion, and admin override is written here and never mutated — the evidence trail."""

    __tablename__ = "certification_events"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_consultant_id: Mapped[UUID] = mapped_column(
        ForeignKey("consultants.id"), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="", nullable=False)
    from_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by_consultant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class CalibrationSessionORM(Base):
    """A calibration round (GRS-0022, Methodology §9). Owner = the facilitator. The vignettes are
    stored as JSON; the computed result is stamped into ``results_json`` on close (immutable
    thereafter). Status gates the blind: OPEN collects ratings, CLOSED reveals the result."""

    __tablename__ = "calibration_sessions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # THE scoping column — the facilitator; sessions are readable org-wide (shared content).
    owner_consultant_id: Mapped[UUID] = mapped_column(
        ForeignKey("consultants.id"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False)
    vignettes_json: Mapped[str] = mapped_column(Text, nullable=False)
    results_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class CalibrationRatingORM(Base):
    """One assessor's blind rating set for a session (GRS-0022). ``owner_consultant_id`` is the
    assessor; unique per (session, assessor). Locked on submit; contributes to the result only when
    submitted, and is never visible to a co-rater (owner-scoped) or to anyone before close."""

    __tablename__ = "calibration_ratings"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    owner_consultant_id: Mapped[UUID] = mapped_column(
        ForeignKey("consultants.id"), index=True, nullable=False
    )
    session_id: Mapped[UUID] = mapped_column(
        ForeignKey("calibration_sessions.id"), index=True, nullable=False
    )
    entries_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    submitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    __table_args__ = (
        UniqueConstraint(
            "session_id", "owner_consultant_id", name="uq_calibration_rating_session_rater"
        ),
    )


class CommitteeDecisionORM(Base):
    """A Rating Committee's recorded call on one high-stakes item of an assessment (GRS-0021,
    Methodology §8). One row per (assessment, item_type, item_key) — a re-decision updates it in
    place. ``owner_consultant_id`` is the assessment's owner (scoping); ``decided_by_consultant_id``
    is the committee member who made the call (never the owner — peer challenge)."""

    __tablename__ = "committee_decisions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # THE scoping column — the assessment owner; committee visibility is widened in the repo.
    owner_consultant_id: Mapped[UUID] = mapped_column(
        ForeignKey("consultants.id"), index=True, nullable=False
    )
    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.id"), index=True, nullable=False
    )
    item_type: Mapped[str] = mapped_column(String(16), nullable=False)
    item_key: Mapped[str] = mapped_column(String(64), nullable=False)
    rating: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    dissent_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by_consultant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "item_type",
            "item_key",
            name="uq_committee_decision_assessment_item",
        ),
    )


class ModuleRatingDraftORM(Base):
    """One rater's independent, blind rating of one module's subcomponents (GRS-0020, Methodology
    §9 dual rating). ``owner_consultant_id`` is the rater. The (assessment, module, rater) triple is
    unique — a rater is assigned to a module once. ``ratings_json`` holds the rater's
    ``SubcomponentRating`` tuple; ``submitted`` locks it (the blind opens only when every assigned
    rater on the module has submitted). Consensus is then resolved into the assessment document."""

    __tablename__ = "module_rating_drafts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # THE scoping column — the rater who owns this draft.
    owner_consultant_id: Mapped[UUID] = mapped_column(
        ForeignKey("consultants.id"), index=True, nullable=False
    )
    assessment_id: Mapped[UUID] = mapped_column(
        ForeignKey("assessments.id"), index=True, nullable=False
    )
    module_key: Mapped[str] = mapped_column(String(64), nullable=False)
    ratings_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    submitted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    __table_args__ = (
        UniqueConstraint(
            "assessment_id",
            "module_key",
            "owner_consultant_id",
            name="uq_module_rating_draft_assessment_module_rater",
        ),
    )


class ScoringRunORM(Base):
    """An immutable, versioned, content-hashed scoring run (CLAUDE.md non-negotiable #6).

    Append-only: rows are inserted, never updated — the ONE exception is finalisation, which flips
    ``finalised`` False→True and locks the inputs. The full inputs and result (every intermediate)
    are stored as JSON text so a run is reproducible and tamper-evident: the content hash is taken
    over inputs + the three versions, and can be recomputed from the stored inputs to prove the row
    was not altered. Scoped by ``owner_consultant_id`` like every owned resource.
    """

    __tablename__ = "scoring_runs"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # THE scoping column — every read/list is filtered by this in the repository layer.
    owner_consultant_id: Mapped[UUID] = mapped_column(
        ForeignKey("consultants.id"), index=True, nullable=False
    )
    assessment_id: Mapped[UUID] = mapped_column(Uuid, index=True, nullable=False)

    # Version stamps — a run is only meaningful against the code + coefficients that produced it.
    engine_version: Mapped[str] = mapped_column(String(64), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(64), nullable=False)
    coefficient_version: Mapped[str] = mapped_column(String(128), nullable=False)
    # Which uncertainty model produced the band (§7, ADR-0008); null for a point-only run.
    uncertainty_version: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # The immutability seal: SHA-256 over the canonical inputs + the three versions. Indexed (not
    # unique — a legitimate re-run of identical inputs is a new append-only row with the same hash).
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # The immutable record: canonical JSON of the inputs and the full result (every intermediate).
    inputs_json: Mapped[str] = mapped_column(Text, nullable=False)
    result_json: Mapped[str] = mapped_column(Text, nullable=False)

    # Denormalised score-domain summary for cheap listing/querying (also present in result_json).
    v_index: Mapped[float | None] = mapped_column(Float, nullable=True)
    v_p10: Mapped[float | None] = mapped_column(Float, nullable=True)
    v_p90: Mapped[float | None] = mapped_column(Float, nullable=True)
    uncertainty_rating: Mapped[str | None] = mapped_column(String(16), nullable=True)

    finalised: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class AssessmentORM(Base):
    """A scoped, lifecycle-managed assessment (GRS-0009). The intermediate document is stored as
    JSON so a partial, half-filled assessment saves without scoring (autosave). Editing is refused
    once ``state`` is finalised; the immutable scoring run is linked via ``scoring_run_id``."""

    __tablename__ = "assessments"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # THE scoping column — every read/list/update is filtered by this in the repository layer.
    owner_consultant_id: Mapped[UUID] = mapped_column(
        ForeignKey("consultants.id"), index=True, nullable=False
    )
    subject: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    state: Mapped[str] = mapped_column(String(16), default="draft", nullable=False)
    document_json: Mapped[str] = mapped_column(Text, nullable=False)

    finalised_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scoring_run_id: Mapped[UUID | None] = mapped_column(Uuid, nullable=True)
    # Version stamps recorded at finalisation (null while editable).
    engine_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    methodology_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    coefficient_version: Mapped[str | None] = mapped_column(String(128), nullable=True)
    uncertainty_version: Mapped[str | None] = mapped_column(String(128), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
