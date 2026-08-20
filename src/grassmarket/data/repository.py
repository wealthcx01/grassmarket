"""The repository — the ONE data-access layer (CLAUDE.md non-negotiables #5 and #9).

Two jobs, both structural:

1. **Centralise persistence.** Every query in the app lives here. Feature code calls methods,
   never SQLAlchemy. The method surface is shaped like the future Holy Corner API resources, so
   the backing store can swap from Postgres to that API without touching callers.
2. **Enforce absolute data scoping.** A consultant sees only their own owned resources. This is
   enforced in exactly one place — `_assert_can_access` — and tested from day one. There is no
   second code path that could forget the check.

Fail-loud throughout: a missing row raises `NotFoundError`; a cross-owner access raises
`ScopeViolationError`. Nothing is silently filtered into an empty success or defaulted around.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID

from bcap_contracts.arena import (
    ArenaModuleTarget,
    ArenaPowerTarget,
    ArenaScenario,
    ArenaScore,
    ArenaSession,
    ArenaStatus,
    ArenaTurn,
)
from bcap_contracts.assessments import (
    Assessment,
    AssessmentDocument,
    AssessmentState,
    BrokeragePortfolioEntry,
    ModuleRatingDraft,
    RecordProvenance,
    ScoringRun,
    SubcomponentRating,
)
from bcap_contracts.audit import AuditEvent, AuditEventType, PersonalDataExport
from bcap_contracts.auth import Consultant
from bcap_contracts.bench import BenchQueue, PerformanceSummary
from bcap_contracts.calibration import (
    CalibrationRating,
    CalibrationResult,
    CalibrationSession,
    CalibrationStatus,
    CalibrationVignette,
    RatingEntry,
)
from bcap_contracts.certification import (
    CertificationEvent,
    CertificationEventKind,
    CertificationRecord,
    CourseCertification,
)
from bcap_contracts.client_report import SECTION_ORDER, ReportSectionKind
from bcap_contracts.commissions import (
    CommissionKind,
    CommissionLine,
    CommissionStream,
    DeliveryType,
    EarningsSummary,
    EarningsTimeline,
    EarningsTimelinePoint,
    PaymentStatus,
    SourcingAttribution,
    load_commission_config,
)
from bcap_contracts.committee import (
    CommitteeDecision,
    CommitteeDecisionStatus,
    CommitteeItemType,
)
from bcap_contracts.common import (
    AssessorLevel,
    ConsultantTier,
    EvidenceGrade,
    NonScoreState,
    Role,
    UncertaintyRating,
)
from bcap_contracts.deliverables import (
    ApprovalStatus,
    Deliverable,
    DeliverableIndexRow,
    DeliverableMode,
    DeliverableType,
)
from bcap_contracts.engagements import (
    CommsChannel,
    CommsLogEntry,
    DeliverableSlot,
    Engagement,
    EngagementStatus,
    Workshop,
    WorkshopState,
)
from bcap_contracts.entities import (
    Contact,
    PipelineStage,
    Prospect,
    RegistryContact,
    RegistryTarget,
)
from bcap_contracts.extraction import (
    Extraction,
    ExtractionConfidence,
    ExtractionStatus,
    FieldProvenance,
)
from bcap_contracts.fees import (
    RecoveryFeeAttribution,
    RecoveryFeeConfig,
    load_recovery_fee_config,
)
from bcap_contracts.founder_review import (
    FounderApproval,
    FounderReviewQueueEntry,
)
from bcap_contracts.learning import (
    CertificationCredit,
    ContentCompletion,
    Course,
    CourseTree,
    CourseVersion,
    DrillCard,
    GeneratedQuiz,
    LearningKind,
    LearningModule,
    Lesson,
    LessonCompletion,
    QuizQuestion,
    QuizStatus,
    SectionProgress,
    SectionTestAttempt,
)
from bcap_contracts.meetings import MediaKind, MeetingTranscript
from bcap_contracts.money import Currency, Money
from bcap_contracts.narratives import AINarrative, NarrativeSection, NarrativeStatus
from bcap_contracts.pipeline import StageHistoryEntry, assert_legal_transition
from bcap_contracts.predictions import (
    BenchmarkRow,
    BenchmarkSector,
    CBenchmarkRow,
    Prediction,
    PredictionOutcome,
)
from bcap_contracts.prospecting import (
    ProspectingPage,
    ProspectingTarget,
    looks_like_a_domain_stem,
    segment_label,
)
from bcap_contracts.report_links import (
    ClientReportLink,
    ReportReadEvent,
    ReportReadReport,
    SectionReadSummary,
)
from sqlalchemy import Text, delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from grassmarket.atlas import AssessmentInputs, AtlasResult
from grassmarket.data.database import Base
from grassmarket.data.models import (
    AINarrativeORM,
    ArenaScenarioORM,
    ArenaSessionORM,
    AssessmentORM,
    AuditEventORM,
    BenchmarkRowORM,
    CalibrationRatingORM,
    CalibrationSessionORM,
    CBenchmarkRowORM,
    CertificationEventORM,
    CertificationRecordORM,
    ClientReportLinkORM,
    ClientReportProseORM,
    CommissionLineORM,
    CommitteeDecisionORM,
    CommsLogEntryORM,
    ConsultantORM,
    ContactORM,
    ContentCompletionORM,
    CourseORM,
    CourseVersionORM,
    DeliverableORM,
    DrillCardORM,
    EngagementORM,
    ExtractionORM,
    FieldProvenanceORM,
    FounderApprovalORM,
    GeneratedQuizORM,
    InvitationORM,
    LearningModuleORM,
    LessonCompletionORM,
    LoginHandoffCodeORM,
    MeetingTranscriptORM,
    ModuleRatingDraftORM,
    PredictionORM,
    ProspectORM,
    ProspectStageHistoryORM,
    RecoveryFeeAttributionORM,
    RefreshTokenORM,
    RegistryContactORM,
    RegistryTargetORM,
    ReportReadEventORM,
    ScoringRunORM,
    SectionTestAttemptORM,
    WorkshopORM,
)
from grassmarket.earnings.commission import (
    commission_content_hash,
    compute_consultancy_commission,
    compute_product_commission,
)
from grassmarket.entities.registry import rank_name
from grassmarket.pathb.cipher import TranscriptCipher
from grassmarket.pathb.extraction import Extractor
from grassmarket.pathb.scanning import MediaScanner
from grassmarket.pathb.transcription import Transcriber, TranscriptionError
from grassmarket.pipeline.fees import attribution_content_hash, is_within_attribution_window
from grassmarket.predictions.logic import PredictionSpec, score_prediction
from grassmarket.workbench.arena import ArenaFeedbackDrafter, score_transcript
from grassmarket.workbench.bench import (
    assemble_queue,
    pick_arena_scenario,
    pick_next_coursework,
    pick_research_prospect,
    summarise_performance,
)
from grassmarket.workbench.calibration import compute_calibration_result
from grassmarket.workbench.certification import next_level, promotion_blockers
from grassmarket.workbench.course_certs import (
    CourseCertSubject,
    course_cert_status,
    course_cert_subjects,
    signoff_blockers,
)
from grassmarket.workbench.courses import (
    approve_lesson_in_tree,
    is_course_complete,
    unapproved_ai_lessons,
)
from grassmarket.workbench.drills import PASSING_GRADE, DrillState, next_due, review

# Stages at which a prospect is "contracted or beyond" — the only prospects an engagement may link.
_ENGAGEABLE_STAGES = frozenset(
    {PipelineStage.CONTRACTED, PipelineStage.ACTIVE, PipelineStage.DELIVERED}
)


def content_hash_for(
    inputs: AssessmentInputs,
    engine_version: str,
    methodology_version: str,
    coefficient_version: str,
) -> str:
    """SHA-256 over the canonical inputs + the three versions — the immutability seal of a scoring
    run (CLAUDE.md non-negotiable #6). Deterministic: identical inputs and versions always hash the
    same, so a stored hash can be recomputed to prove the row was not altered."""
    canonical = "|".join(
        [engine_version, methodology_version, coefficient_version, inputs.model_dump_json()]
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _add_months(start: date, months: int) -> date:
    """`start` advanced by whole `months`, clamping the day to the target month's length. Used to
    stamp a Stream-A product commission's window cut-off (ADR-0026)."""
    total = start.month - 1 + months
    year = start.year + total // 12
    month = total % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _strip_governance_fields(document: AssessmentDocument) -> AssessmentDocument:
    """Return a copy of the document with every subcomponent's dual-rating governance fields reset
    to their unrated defaults. Only `resolve_module_consensus` (which computes them from real
    drafts) may set them — an autosave never carries forgeable governance (ADR-0010, §9)."""
    return document.model_copy(
        update={
            "subcomponents": tuple(
                s.model_copy(update={"rater_ids": (), "consensus": False, "dissent_note": None})
                for s in document.subcomponents
            )
        }
    )


_HIGH_EVIDENCE = (EvidenceGrade.E3_ARTIFACT, EvidenceGrade.E4_OBSERVED)


def _cap_grade(grade: EvidenceGrade | None) -> EvidenceGrade | None:
    """Knock an artifact-level grade down to E1 (used where no artifact link can exist)."""
    return EvidenceGrade.E1_SELF_REPORTED if grade in _HIGH_EVIDENCE else grade


# A sentinel actor id for system-originated audit events (no human actor).
_SYSTEM_ACTOR = UUID(int=0)

# Pagination bounds for list endpoints. A caller may never pull an unbounded result set (an
# append-only table like the audit log or benchmark population grows without limit) — the default
# caps an unparameterised call and the max caps a hostile one.
DEFAULT_PAGE_LIMIT = 100
MAX_PAGE_LIMIT = 500


def _clamp_limit(limit: int | None) -> int:
    """Resolve a page size to the allowed range: unset → default, else clamp to [1, max]."""
    if limit is None:
        return DEFAULT_PAGE_LIMIT
    return max(1, min(limit, MAX_PAGE_LIMIT))


def _document_coverage(document: object, registry_view) -> float | None:
    """Assessed subcomponents over APPLICABLE ones (Not Applicable excluded), measured against the
    assessment's OWN operating-model view (GRS-0168) — a wealth/exchange assessment is judged on
    its profile's subcomponents, never the full retail superset. Using the superset produced the
    staging-rerun contradiction: a fully-rated 24-subcomponent exchange assessment showed
    "Completeness 47%" (24/51) beside the wizard's "100% of applicable". Rows outside the view
    (e.g. after a profile switch) are ignored, matching the live panel's coverage notion."""
    legal = registry_view.all_subcomponent_keys()
    subs = [r for r in getattr(document, "subcomponents", ()) if r.subcomponent_key in legal]
    assessed = sum(1 for r in subs if r.level is not None)
    not_applicable = sum(1 for r in subs if r.state == NonScoreState.NOT_APPLICABLE)
    applicable = len(legal) - not_applicable
    return round(assessed / applicable, 4) if applicable > 0 else None


def _owned_orm_classes() -> list[type]:
    """Every mapped ORM that carries `owner_consultant_id` — found by reflection so GDPR export and
    deletion cover ALL owned tables, present and future, with no hand-maintained list to drift."""
    classes: list[type] = []
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if "owner_consultant_id" in cls.__table__.columns:
            classes.append(cls)
    return classes


def _json_safe(value: object) -> object:
    """Make an ORM column value JSON-serialisable for a GDPR export. Raw ciphertext is not exported
    as bytes — the encrypted transcript is marked, not dumped."""
    if isinstance(value, bytes):
        return "[encrypted]"
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def _row_to_dict(row: object, redact: frozenset[str] = frozenset()) -> dict:
    """A JSON-safe dict of an ORM row's columns, named columns redacted (e.g. password hash)."""
    columns = row.__table__.columns  # type: ignore[attr-defined]
    return {
        col.name: "[redacted]" if col.name in redact else _json_safe(getattr(row, col.name))
        for col in columns
    }


def _cap_extraction_evidence(document: AssessmentDocument) -> AssessmentDocument:
    """Extracted ratings default to E1 and are never above E2 without an artifact (GRS-0030, PRD
    §3.3): AI cannot manufacture a high evidence grade from a transcript alone. For a SUBCOMPONENT
    E3/E4 grade with no `evidence_refs` is knocked to E1. A POWER carries no evidence-ref field at
    all, so an extracted power grade can never be artifact-backed — every E3/E4 benefit/barrier
    is unconditionally knocked to E1 (these grades drive the Monte Carlo uncertainty band)."""
    capped_subs = tuple(
        s.model_copy(update={"evidence_grade": EvidenceGrade.E1_SELF_REPORTED})
        if s.evidence_grade in _HIGH_EVIDENCE and not s.evidence_refs
        else s
        for s in document.subcomponents
    )
    capped_powers = tuple(
        p.model_copy(
            update={
                "benefit_grade": _cap_grade(p.benefit_grade),
                "barrier_grade": _cap_grade(p.barrier_grade),
            }
        )
        for p in document.powers
    )
    return document.model_copy(update={"subcomponents": capped_subs, "powers": capped_powers})


class RepositoryError(Exception):
    """Base class for repository failures. Never swallowed."""


class NotFoundError(RepositoryError):
    """A requested resource does not exist."""


class ScopeViolationError(RepositoryError):
    """A principal attempted to access a resource they do not own. The absolute-scoping guard."""


class ConflictError(RepositoryError):
    """A uniqueness/state conflict (e.g. duplicate email, already-accepted invitation)."""


class WorkshopStateError(RepositoryError):
    """An operation invalid for the workshop's state (e.g. attributing a fee to a not-yet-delivered
    workshop). Fail loud rather than fabricate a delivered date."""


class AttributionWindowExpired(RepositoryError):
    """The prospect contracted outside the recovery-fee attribution window — not eligible. Refusal,
    never a silently-recorded (and unearned) fee."""


def _loose_name(value: str) -> str:
    """A company name reduced for comparison: lower-case, alphanumerics only (GRS-0241).

    Punctuation, spacing and ACCENTS are where the same firm is written two ways ("Deutsche
    Borse" vs "Deutsche Börse AG"), and none of it distinguishes one firm from another.

    The NFKD decomposition is load-bearing and was added after the first version got it wrong:
    stripping non-ASCII directly turns "Börse" into "brse", so "Deutsche Börse" and "Deutsche
    Borse" compared as DIFFERENT firms and the guard would have refused a correct link. Decomposing
    first splits "ö" into "o" + combining diaeresis, and only the mark is dropped.

    Deliberately NOT a fuzzy/edit-distance match: a near-miss score would make the guard
    unpredictable exactly where it matters, and this check refuses rather than merely warns.
    """
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    return re.sub(r"[^a-z0-9]", "", decomposed)


class EngagementLinkError(RepositoryError):
    """An engagement was asked to link something it may not — a prospect that isn't contracted, or
    an assessment that isn't the owner's or isn't finalised. Fail loud rather than link loosely."""


class EngagementSubjectMismatchError(EngagementLinkError):
    """The assessment is about a different firm than the engagement is for (GRS-0241).

    A subclass rather than a flag so a caller can catch *this* case and offer the confirm path,
    while every existing `except EngagementLinkError` keeps refusing as before — the safe direction
    for code written before this check existed.
    """


@dataclass(frozen=True)
class Principal:
    """The authenticated identity every scoped call is made on behalf of. Produced by the auth
    layer from the JWT; consumed here to scope. `consultant_id` is the owner key."""

    consultant_id: UUID
    role: Role
    # The founder review gate (ADR-0041). Derived at token mint from the configured reviewer
    # email rather than stored as a role, so rotating the reviewer is an env change plus a
    # re-login and never a migration. Defaults to False so every existing construction of a
    # Principal is unaffected and no caller acquires the claim by accident.
    is_founder: bool = False
    # Set ONLY while an admin is acting as another consultant (GRS-0208). It is attribution, never
    # authority: `_assert_can_access` does not read it, and it cannot widen what this principal can
    # see. During act-as the principal IS the subject — `consultant_id` and `role` are theirs — so
    # every existing scoping test holds unchanged and the admin is NARROWED rather than extended.
    # That direction is the whole safety argument: act-as can only ever show less.
    acting_admin_id: UUID | None = None

    @property
    def is_acting_as(self) -> bool:
        return self.acting_admin_id is not None

    @property
    def is_admin(self) -> bool:
        return self.role is Role.ADMIN

    @property
    def is_committee(self) -> bool:
        """A Rating Committee member (Methodology §8). Widens visibility of the committee queue and
        permits sign-off — but never on the member's own assessment (peer challenge)."""
        return self.role is Role.COMMITTEE_MEMBER


@dataclass(frozen=True)
class StoredConsultant:
    """Internal identity record INCLUDING the password hash — used only by the auth layer, never
    returned from the API. Convert to the public `Consultant` contract with `to_contract()`."""

    id: UUID
    email: str
    full_name: str
    hashed_password: str | None  # None for an OAuth-only account (ADR-0024)
    role: Role
    tier: ConsultantTier
    assessor_level: AssessorLevel
    is_active: bool
    created_at: datetime
    updated_at: datetime
    google_sub: str | None = None  # bound on first Google sign-in (ADR-0024)

    def to_contract(self) -> Consultant:
        return Consultant(
            id=self.id,
            email=self.email,
            full_name=self.full_name,
            role=self.role,
            tier=self.tier,
            assessor_level=self.assessor_level,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


@dataclass(frozen=True)
class StoredScoringRun:
    """The full immutable scoring-run record, including the stored inputs/result JSON — used to
    verify integrity (recompute the content hash) and to re-score. Not returned from the API as-is;
    the public shape is the `ScoringRun` contract."""

    id: UUID
    owner_consultant_id: UUID
    assessment_id: UUID
    engine_version: str
    methodology_version: str
    coefficient_version: str
    content_hash: str
    inputs_json: str
    result_json: str
    finalised: bool


class Repository:
    """Wraps a SQLAlchemy session. One instance per request (see web dependencies)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ------------------------------------------------------------------ scoping guard
    def _assert_can_access(self, principal: Principal, owner_id: UUID) -> None:
        """The single scoping decision. An owner sees their own; an admin sees all; everyone else
        is refused loudly. Every scoped method routes through here — there is no bypass."""
        if principal.is_admin:
            return
        if owner_id != principal.consultant_id:
            raise ScopeViolationError(
                "Principal is not permitted to access a resource owned by another consultant. "
                "Data scoping is absolute (CLAUDE.md non-negotiable #9)."
            )

    # ------------------------------------------------------------------ identity (UNSCOPED)
    # These are system-level identity lookups used ONLY by the auth layer. They are not owned
    # resources; they must not be exposed as scoped feature data.
    def get_consultant_by_email(self, email: str) -> StoredConsultant | None:
        row = self._session.execute(
            select(ConsultantORM).where(ConsultantORM.email == email.lower())
        ).scalar_one_or_none()
        return self._to_stored_consultant(row) if row is not None else None

    def get_consultant_by_id(self, consultant_id: UUID) -> StoredConsultant | None:
        row = self._session.get(ConsultantORM, consultant_id)
        return self._to_stored_consultant(row) if row is not None else None

    def set_consultant_password(self, consultant_id: UUID, hashed_password: str) -> None:
        """Replace a consultant's password hash (GRS-0148d). Persistence-only — the caller (the auth
        service) verifies the current password and hashes the new one. Fail loud if absent."""
        row = self._session.get(ConsultantORM, consultant_id)
        if row is None:
            raise NotFoundError(f"No consultant {consultant_id}.")
        row.hashed_password = hashed_password
        self._session.add(row)
        self._session.flush()

    def create_consultant(
        self,
        *,
        email: str,
        full_name: str,
        hashed_password: str | None,
        role: Role,
        tier: ConsultantTier,
        assessor_level: AssessorLevel = AssessorLevel.TRAINED,
    ) -> StoredConsultant:
        email = email.lower()
        if self.get_consultant_by_email(email) is not None:
            raise ConflictError(f"A consultant with email {email!r} already exists.")
        row = ConsultantORM(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            tier=tier,
            assessor_level=assessor_level,
        )
        self._session.add(row)
        self._session.flush()
        return self._to_stored_consultant(row)

    # ------------------------------------------------------------------ invitations (UNSCOPED)
    def create_invitation(
        self,
        *,
        email: str,
        token_hash: str,
        role: Role,
        tier: ConsultantTier,
        invited_by_consultant_id: UUID,
        expires_at: datetime,
    ) -> InvitationORM:
        row = InvitationORM(
            email=email.lower(),
            token_hash=token_hash,
            role=role,
            tier=tier,
            invited_by_consultant_id=invited_by_consultant_id,
            expires_at=expires_at,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def get_invitation_by_token_hash(self, token_hash: str) -> InvitationORM | None:
        return self._session.execute(
            select(InvitationORM).where(InvitationORM.token_hash == token_hash)
        ).scalar_one_or_none()

    def mark_invitation_accepted(self, invitation: InvitationORM, accepted_at: datetime) -> None:
        if invitation.accepted_at is not None:
            raise ConflictError("Invitation has already been accepted.")
        invitation.accepted_at = accepted_at
        self._session.add(invitation)
        self._session.flush()

    # ------------------------------------------------------------------ prospects (SCOPED)
    def create_prospect(
        self,
        principal: Principal,
        *,
        company_name: str,
        stage: PipelineStage = PipelineStage.PROSPECT,
        sector: str | None = None,
        website: str | None = None,
        primary_contact_name: str | None = None,
        primary_contact_email: str | None = None,
        notes: str | None = None,
        registry_target_id: str | None = None,
    ) -> Prospect:
        """Create a prospect owned by the principal. A consultant can only create for themselves —
        the owner is taken from the principal, never from caller-supplied input.

        `registry_target_id` records that this prospect was CLAIMED from the shared registry
        (GRS-0238), so the Prospecting page can tell an advisor what they are already working
        without matching on names. Optional, because a prospect typed by hand has no such origin
        and inventing one would be a fabricated link."""
        row = ProspectORM(
            owner_consultant_id=principal.consultant_id,
            company_name=company_name,
            stage=stage,
            sector=sector,
            website=website,
            primary_contact_name=primary_contact_name,
            primary_contact_email=primary_contact_email,
            notes=notes,
            registry_target_id=registry_target_id,
        )
        self._session.add(row)
        self._session.flush()
        # The creation row of the stage timeline (from_stage NULL). Same choke-point discipline as
        # update_prospect_stage — every stage a prospect has ever held is recorded here.
        self._record_stage_history(row, from_stage=None, to_stage=PipelineStage(row.stage))
        self._session.flush()
        return self._to_prospect(row)

    def list_prospects(self, principal: Principal) -> list[Prospect]:
        """Only the principal's own prospects (admins see all). The scope is applied in the query
        AND every returned row is re-checked — belt and braces."""
        stmt = select(ProspectORM)
        if not principal.is_admin:
            stmt = stmt.where(ProspectORM.owner_consultant_id == principal.consultant_id)
        rows = self._session.execute(stmt.order_by(ProspectORM.created_at)).scalars().all()
        result: list[Prospect] = []
        for row in rows:
            self._assert_can_access(principal, row.owner_consultant_id)
            result.append(self._to_prospect(row))
        return result

    def get_prospect(self, principal: Principal, prospect_id: UUID) -> Prospect:
        row = self._session.get(ProspectORM, prospect_id)
        if row is None:
            raise NotFoundError(f"Prospect {prospect_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        return self._to_prospect(row)

    def update_prospect_stage(
        self, principal: Principal, prospect_id: UUID, stage: PipelineStage
    ) -> Prospect:
        """Move a prospect to a new stage. The move must be legal per the lifecycle graph — an
        illegal jump (or a no-op to the same stage) raises `IllegalStageTransition`, never a silent
        allow. On a valid move `stage_entered_at` is reset so time-in-stage restarts."""
        row = self._session.get(ProspectORM, prospect_id)
        if row is None:
            raise NotFoundError(f"Prospect {prospect_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        from_stage = PipelineStage(row.stage)
        assert_legal_transition(from_stage, stage)
        moved_at = datetime.now(UTC)
        row.stage = stage
        row.stage_entered_at = moved_at
        self._session.add(row)
        # Record the transition at the same choke-point that mutates the stage — a move can't happen
        # without leaving a timeline row (audit + the CRM history view, GRS-0111).
        self._record_stage_history(row, from_stage=from_stage, to_stage=stage, occurred_at=moved_at)
        self._session.flush()
        return self._to_prospect(row)

    def _record_stage_history(
        self,
        prospect: ProspectORM,
        *,
        from_stage: PipelineStage | None,
        to_stage: PipelineStage,
        occurred_at: datetime | None = None,
    ) -> None:
        """Append one stage-history row, inheriting the prospect's owner (scoping travels here)."""
        self._session.add(
            ProspectStageHistoryORM(
                owner_consultant_id=prospect.owner_consultant_id,
                prospect_id=prospect.id,
                from_stage=from_stage.value if from_stage is not None else None,
                to_stage=to_stage.value,
                occurred_at=occurred_at if occurred_at is not None else datetime.now(UTC),
            )
        )

    def list_stage_history(
        self, principal: Principal, prospect_id: UUID
    ) -> tuple[StageHistoryEntry, ...]:
        """The prospect's stage timeline, oldest first. Owner-scoped: the prospect must be visible
        to the principal (a scoping failure raises before any history is returned)."""
        prospect = self._session.get(ProspectORM, prospect_id)
        if prospect is None:
            raise NotFoundError(f"Prospect {prospect_id} not found.")
        self._assert_can_access(principal, prospect.owner_consultant_id)
        stmt = (
            select(ProspectStageHistoryORM)
            .where(ProspectStageHistoryORM.prospect_id == prospect_id)
            .order_by(ProspectStageHistoryORM.occurred_at, ProspectStageHistoryORM.created_at)
        )
        rows = self._session.execute(stmt).scalars().all()
        return tuple(
            StageHistoryEntry(
                prospect_id=r.prospect_id,
                from_stage=PipelineStage(r.from_stage) if r.from_stage is not None else None,
                to_stage=PipelineStage(r.to_stage),
                occurred_at=r.occurred_at,
            )
            for r in rows
        )

    def update_prospect(
        self,
        principal: Principal,
        prospect_id: UUID,
        *,
        company_name: str | None = None,
        sector: str | None = None,
        website: str | None = None,
        primary_contact_name: str | None = None,
        primary_contact_email: str | None = None,
        notes: str | None = None,
    ) -> Prospect:
        """Patch a prospect's editable fields (GRS-0111) — owner-scoped. Only the fields passed (not
        None) are changed; stage moves stay on the dedicated choke-point `update_prospect_stage`.
        An empty-string `company_name` is refused (it is required)."""
        row = self._session.get(ProspectORM, prospect_id)
        if row is None:
            raise NotFoundError(f"Prospect {prospect_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        if company_name is not None:
            if not company_name.strip():
                raise ConflictError("A prospect's company name cannot be empty.")
            row.company_name = company_name
        if sector is not None:
            row.sector = sector or None
        if website is not None:
            row.website = website or None
        if primary_contact_name is not None:
            row.primary_contact_name = primary_contact_name or None
        if primary_contact_email is not None:
            row.primary_contact_email = primary_contact_email or None
        if notes is not None:
            row.notes = notes or None
        self._session.add(row)
        self._session.flush()
        return self._to_prospect(row)

    # ------------------------------------------------------------------ contacts (SCOPED, GRS-0111)
    def create_contact(
        self,
        principal: Principal,
        prospect_id: UUID,
        *,
        name: str,
        email: str | None = None,
        phone: str | None = None,
        title: str | None = None,
        is_primary: bool = False,
    ) -> Contact:
        """Add a contact to a prospect the caller owns. Making it primary demotes any other primary
        and mirrors the name/email onto the prospect (the win-probability scorer reads those)."""
        prospect = self._session.get(ProspectORM, prospect_id)
        if prospect is None:
            raise NotFoundError(f"Prospect {prospect_id} not found.")
        self._assert_can_access(principal, prospect.owner_consultant_id)
        row = ContactORM(
            owner_consultant_id=prospect.owner_consultant_id,
            prospect_id=prospect_id,
            name=name,
            email=email or None,
            phone=phone or None,
            title=title or None,
            is_primary=is_primary,
        )
        self._session.add(row)
        self._session.flush()
        if is_primary:
            self._make_contact_primary(prospect, row)
        self._session.flush()
        return self._to_contact(row)

    def list_contacts(self, principal: Principal, prospect_id: UUID) -> list[Contact]:
        """Every contact on a prospect the caller owns — primary first, then by creation."""
        prospect = self._session.get(ProspectORM, prospect_id)
        if prospect is None:
            raise NotFoundError(f"Prospect {prospect_id} not found.")
        self._assert_can_access(principal, prospect.owner_consultant_id)
        stmt = (
            select(ContactORM)
            .where(ContactORM.prospect_id == prospect_id)
            .order_by(ContactORM.is_primary.desc(), ContactORM.created_at)
        )
        return [self._to_contact(r) for r in self._session.execute(stmt).scalars()]

    def update_contact(
        self,
        principal: Principal,
        contact_id: UUID,
        *,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        title: str | None = None,
        is_primary: bool | None = None,
    ) -> Contact:
        """Patch a contact the caller owns. Setting `is_primary` True demotes the others + mirrors
        the prospect's primary_contact_* fields."""
        row = self._session.get(ContactORM, contact_id)
        if row is None:
            raise NotFoundError(f"Contact {contact_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        if name is not None:
            if not name.strip():
                raise ConflictError("A contact's name cannot be empty.")
            row.name = name
        if email is not None:
            row.email = email or None
        if phone is not None:
            row.phone = phone or None
        if title is not None:
            row.title = title or None
        self._session.add(row)
        if is_primary:
            prospect = self._require_consultant_owned_prospect(row.prospect_id)
            self._make_contact_primary(prospect, row)
        self._session.flush()
        return self._to_contact(row)

    def delete_contact(self, principal: Principal, contact_id: UUID) -> None:
        """Remove a contact the caller owns. If it was primary, the prospect's mirrored primary_*
        fields are cleared (the caller can promote another contact)."""
        row = self._session.get(ContactORM, contact_id)
        if row is None:
            raise NotFoundError(f"Contact {contact_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        if row.is_primary:
            prospect = self._session.get(ProspectORM, row.prospect_id)
            if prospect is not None:
                prospect.primary_contact_name = None
                prospect.primary_contact_email = None
                self._session.add(prospect)
        self._session.delete(row)
        self._session.flush()

    # ------------------------------------------------- GTM registry (NETWORK-SHARED, GRS-0193)
    # ADR-0045 §2: the target/contact registry is shared reference data, not a consultant's own
    # records, so these reads take no owner filter. That is the ONE deliberate exception to
    # non-negotiable #9, and `tests/test_gtm_registry.py` asserts both halves of it: the registry
    # is readable by any authenticated consultant, and a prospect's own `contacts` stay private.
    # The write side is operator/ingest-only and never reachable from an advisor-facing route.

    def upsert_registry_target(self, target: RegistryTarget) -> RegistryTarget:
        """Insert or overwrite a registry target by its `target_id`. Idempotent by construction:
        re-running an import overwrites the same row rather than duplicating it."""
        row = self._session.get(RegistryTargetORM, target.target_id)
        if row is None:
            row = RegistryTargetORM(target_id=target.target_id)
        row.name = target.name
        row.aliases = list(target.aliases)
        row.domain = target.domain
        row.segment = target.segment
        row.country = target.country
        row.ric = target.ric
        row.ctb_id = target.ctb_id
        row.source = target.source
        row.imported_on = target.imported_on
        self._session.add(row)
        self._session.flush()
        return self._to_registry_target(row)

    def upsert_registry_contact(self, contact: RegistryContact) -> RegistryContact:
        """Insert or overwrite a registry contact by its `contact_id`. Fails loud if the target is
        unknown: a contact with no institution is not importable (#3)."""
        if self._session.get(RegistryTargetORM, contact.target_id) is None:
            raise NotFoundError(f"Registry target '{contact.target_id}' not found.")
        row = self._session.get(RegistryContactORM, contact.contact_id)
        if row is None:
            row = RegistryContactORM(contact_id=contact.contact_id)
        row.target_id = contact.target_id
        row.full_name = contact.full_name
        row.email = contact.email
        row.phone = contact.phone
        row.job_role = contact.job_role
        row.linkedin = contact.linkedin
        row.verified = contact.verified
        row.source = contact.source
        row.imported_on = contact.imported_on
        self._session.add(row)
        self._session.flush()
        return self._to_registry_contact(row)

    def search_registry_targets(self, query: str, *, limit: int = 8) -> list[RegistryTarget]:
        """Ranked targets matching `query`, using the same exact > prefix > alias > substring order
        the stub registry applies, so behaviour is identical and only the corpus is larger.

        The name filter runs in SQL so the whole imported universe is never loaded; the precise
        ranking then runs over that candidate set, where alias matches (a JSON column, not portably
        queryable) are resolved.
        """
        q = query.strip().lower()
        if not q:
            return []
        like = f"%{q}%"
        # Candidates: a name match in SQL, plus every row whose aliases might match. Aliases are
        # JSON, so they are filtered in Python — bounded by taking only rows that could rank.
        stmt = select(RegistryTargetORM).where(func.lower(RegistryTargetORM.name).like(like))
        by_name = list(self._session.execute(stmt).scalars())
        alias_stmt = select(RegistryTargetORM).where(
            func.lower(func.cast(RegistryTargetORM.aliases, Text)).like(like)
        )
        seen = {r.target_id for r in by_name}
        candidates = by_name + [
            r for r in self._session.execute(alias_stmt).scalars() if r.target_id not in seen
        ]
        ranked: list[tuple[int, str, RegistryTargetORM]] = []
        for row in candidates:
            rank = rank_name(row.name, tuple(row.aliases or ()), q)
            if rank is not None:
                ranked.append((rank, row.name, row))
        ranked.sort(key=lambda t: (t[0], t[1]))
        return [self._to_registry_target(row) for _, _, row in ranked[:limit]]

    def list_registry_targets(
        self,
        principal: Principal,
        *,
        segment: str | None = None,
        country: str | None = None,
        q: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> ProspectingPage:
        """A page of the shared registry, with this advisor's pipeline state joined on (GRS-0238).

        **Two different scoping rules meet here, and keeping them apart is the whole point.** The
        targets are network-shared reference data (ADR-0045 §2) — every advisor browses the same
        imported universe, so there is deliberately no owner filter on them. The
        `already_in_my_pipeline` flag is the opposite: a prospect is one advisor's claim, owner-
        scoped like everything else (#9), so that half is computed against `principal` alone and is
        never cached across principals. `tests/test_prospecting.py` asserts both directions.

        The claim check matches on the registry link first and falls back to an exact,
        case-insensitive company-name match. The fallback exists because every prospect created
        before this ticket has no link, and without it an advisor would be invited to re-add firms
        they are already working. It is an exact match, never fuzzy: the cost of a false positive
        (a real but differently-named firm reads as claimed) is worse than the cost of a false
        negative (a duplicate the advisor can see and delete).
        """
        conditions = []
        if segment:
            conditions.append(RegistryTargetORM.segment == segment)
        if country:
            conditions.append(RegistryTargetORM.country == country)
        if q and q.strip():
            like = f"%{q.strip().lower()}%"
            conditions.append(func.lower(RegistryTargetORM.name).like(like))

        total = int(
            self._session.execute(
                select(func.count(RegistryTargetORM.target_id)).where(*conditions)
            ).scalar_one()
        )
        rows = list(
            self._session.execute(
                select(RegistryTargetORM)
                .where(*conditions)
                .order_by(RegistryTargetORM.name)
                .offset(max(offset, 0))
                .limit(limit)
            ).scalars()
        )
        target_ids = [r.target_id for r in rows]

        counts: dict[str, int] = {}
        if target_ids:
            counts = {
                tid: int(n)
                for tid, n in self._session.execute(
                    select(RegistryContactORM.target_id, func.count(RegistryContactORM.contact_id))
                    .where(RegistryContactORM.target_id.in_(target_ids))
                    .group_by(RegistryContactORM.target_id)
                )
            }

        # Owner-scoped half. Filtered by the principal's own consultant id, so the answer is
        # "already in YOUR pipeline" and cannot leak another advisor's book.
        claimed_ids: set[str] = set()
        claimed_names: set[str] = set()
        if target_ids:
            mine = self._session.execute(
                select(ProspectORM.registry_target_id, ProspectORM.company_name).where(
                    ProspectORM.owner_consultant_id == principal.consultant_id
                )
            )
            for linked_id, company_name in mine:
                if linked_id:
                    claimed_ids.add(linked_id)
                if company_name:
                    claimed_names.add(company_name.strip().lower())

        targets = [
            ProspectingTarget(
                target_id=row.target_id,
                name=row.name,
                domain=row.domain,
                country=row.country,
                segment=row.segment,
                segment_label=segment_label(row.segment)[0],
                segment_kind=segment_label(row.segment)[1],
                source=row.source,
                imported_on=row.imported_on.isoformat(),
                contact_count=counts.get(row.target_id, 0),
                already_in_my_pipeline=(
                    row.target_id in claimed_ids or row.name.strip().lower() in claimed_names
                ),
                name_unverified=looks_like_a_domain_stem(row.name),
            )
            for row in rows
        ]
        return ProspectingPage(targets=targets, total=total, offset=max(offset, 0), limit=limit)

    def registry_segments(self) -> list[tuple[str, int]]:
        """Every segment value present, with its row count — so the filter offers what exists.

        Built from the data rather than from the label map: a source that arrives with a new value
        must show up in the filter as an unlabelled option, not vanish because nobody has written a
        label for it yet.
        """
        rows = self._session.execute(
            select(RegistryTargetORM.segment, func.count(RegistryTargetORM.target_id))
            .where(RegistryTargetORM.segment.is_not(None))
            .group_by(RegistryTargetORM.segment)
            .order_by(func.count(RegistryTargetORM.target_id).desc())
        )
        return [(str(value), int(count)) for value, count in rows]

    def registry_countries(self) -> list[tuple[str, int]]:
        """Every country present, with its row count. Same reasoning as `registry_segments`."""
        rows = self._session.execute(
            select(RegistryTargetORM.country, func.count(RegistryTargetORM.target_id))
            .where(RegistryTargetORM.country.is_not(None))
            .group_by(RegistryTargetORM.country)
            .order_by(RegistryTargetORM.country)
        )
        return [(str(value), int(count)) for value, count in rows]

    def get_registry_target(self, target_id: str) -> RegistryTarget | None:
        row = self._session.get(RegistryTargetORM, target_id)
        return None if row is None else self._to_registry_target(row)

    def count_registry_targets(self) -> int:
        """How many targets are imported. The DB-backed entity registry uses this to decide whether
        the imported universe is live yet, so a fresh dev database still resolves the stub seed."""
        return int(
            self._session.execute(select(func.count(RegistryTargetORM.target_id))).scalar_one()
        )

    def list_registry_contacts(self, target_id: str) -> list[RegistryContact]:
        """Every known contact at an institution — network-shared, verified rows first. Fails loud
        on an unknown target rather than returning an empty list that reads as 'nobody works here'.
        """
        if self._session.get(RegistryTargetORM, target_id) is None:
            raise NotFoundError(f"Registry target '{target_id}' not found.")
        stmt = (
            select(RegistryContactORM)
            .where(RegistryContactORM.target_id == target_id)
            .order_by(RegistryContactORM.verified.desc(), RegistryContactORM.full_name)
        )
        return [self._to_registry_contact(r) for r in self._session.execute(stmt).scalars()]

    @staticmethod
    def _to_registry_target(row: RegistryTargetORM) -> RegistryTarget:
        return RegistryTarget(
            target_id=row.target_id,
            name=row.name,
            aliases=tuple(row.aliases or ()),
            domain=row.domain,
            segment=row.segment,
            country=row.country,
            ric=row.ric,
            ctb_id=row.ctb_id,
            source=row.source,
            imported_on=row.imported_on,
        )

    @staticmethod
    def _to_registry_contact(row: RegistryContactORM) -> RegistryContact:
        return RegistryContact(
            contact_id=row.contact_id,
            target_id=row.target_id,
            full_name=row.full_name,
            email=row.email,
            phone=row.phone,
            job_role=row.job_role,
            linkedin=row.linkedin,
            verified=row.verified,
            source=row.source,
            imported_on=row.imported_on,
        )

    def _require_consultant_owned_prospect(self, prospect_id: UUID) -> ProspectORM:
        prospect = self._session.get(ProspectORM, prospect_id)
        if prospect is None:  # pragma: no cover - a contact always has a prospect
            raise NotFoundError(f"Prospect {prospect_id} not found.")
        return prospect

    def _make_contact_primary(self, prospect: ProspectORM, contact: ContactORM) -> None:
        """Enforce a single primary contact + mirror it onto the prospect (win-prob reads those)."""
        others = self._session.execute(
            select(ContactORM).where(
                ContactORM.prospect_id == prospect.id, ContactORM.id != contact.id
            )
        ).scalars()
        for other in others:
            if other.is_primary:
                other.is_primary = False
                self._session.add(other)
        contact.is_primary = True
        prospect.primary_contact_name = contact.name
        prospect.primary_contact_email = contact.email
        self._session.add_all([contact, prospect])

    @staticmethod
    def _to_contact(row: ContactORM) -> Contact:
        return Contact(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            prospect_id=row.prospect_id,
            name=row.name,
            email=row.email,
            phone=row.phone,
            title=row.title,
            is_primary=row.is_primary,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ------------------------------------------------------------------ workshops (SCOPED)
    def create_workshop(
        self,
        principal: Principal,
        *,
        prospect_id: UUID,
        scheduled_for: date | None = None,
        pre_workshop_brief: str | None = None,
    ) -> Workshop:
        """Schedule a workshop for one of the principal's OWN prospects. The prospect is checked for
        access (a workshop can't be attached to someone else's prospect); the owner is the
        principal, never caller-supplied."""
        # Access check — raises NotFound/ScopeViolation if the prospect isn't the principal's.
        self.get_prospect(principal, prospect_id)
        row = WorkshopORM(
            owner_consultant_id=principal.consultant_id,
            prospect_id=prospect_id,
            state=WorkshopState.SCHEDULED,
            scheduled_for=scheduled_for,
            pre_workshop_brief=pre_workshop_brief,
        )
        self._session.add(row)
        self._session.flush()
        return self._to_workshop(row)

    def get_workshop(self, principal: Principal, workshop_id: UUID) -> Workshop:
        return self._to_workshop(self._require_workshop(principal, workshop_id))

    def list_workshops(self, principal: Principal) -> list[Workshop]:
        stmt = select(WorkshopORM)
        if not principal.is_admin:
            stmt = stmt.where(WorkshopORM.owner_consultant_id == principal.consultant_id)
        rows = self._session.execute(stmt.order_by(WorkshopORM.created_at)).scalars().all()
        result: list[Workshop] = []
        for row in rows:
            self._assert_can_access(principal, row.owner_consultant_id)  # belt and braces
            result.append(self._to_workshop(row))
        return result

    def deliver_workshop(
        self,
        principal: Principal,
        workshop_id: UUID,
        *,
        delivered_on: date,
        workshop_output: str | None = None,
    ) -> Workshop:
        """Mark a scheduled workshop delivered. Re-delivering is refused (state is not re-set)."""
        row = self._require_workshop(principal, workshop_id)
        if row.state == WorkshopState.DELIVERED:
            raise WorkshopStateError(f"Workshop {workshop_id} is already delivered.")
        row.state = WorkshopState.DELIVERED
        row.delivered_on = delivered_on
        if workshop_output is not None:
            row.workshop_output = workshop_output
        self._session.add(row)
        self._session.flush()
        return self._to_workshop(row)

    # ----------------------------------------- recovery-fee attributions (SCOPED, append-only)
    def record_recovery_fee_attribution(
        self,
        principal: Principal,
        workshop_id: UUID,
        *,
        contracted_on: date,
        config: RecoveryFeeConfig | None = None,
    ) -> RecoveryFeeAttribution:
        """Attribute a recovery fee to a DELIVERED workshop whose prospect contracted within the
        config window. Append-only and immutable: the fee is computed from config (by the owner's
        tier), sealed with a content hash, and written once. Outside the window → refusal; a second
        attribution for the same workshop → conflict. The fee £ is `Money` (never a Score)."""
        config = config or load_recovery_fee_config()
        row = self._require_workshop(principal, workshop_id)
        if row.state != WorkshopState.DELIVERED or row.delivered_on is None:
            raise WorkshopStateError(
                f"Workshop {workshop_id} is not delivered; no recovery fee can be attributed."
            )
        if not is_within_attribution_window(
            row.delivered_on, contracted_on, config.attribution_window_days
        ):
            raise AttributionWindowExpired(
                f"Prospect contracted on {contracted_on} — outside the "
                f"{config.attribution_window_days}-day window from delivery on {row.delivered_on}."
            )
        existing = self._session.execute(
            select(RecoveryFeeAttributionORM).where(
                RecoveryFeeAttributionORM.workshop_id == workshop_id
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise ConflictError(
                f"Workshop {workshop_id} already has a recovery-fee attribution; records are "
                f"append-only and immutable."
            )

        # The column is a plain String, so SQLite hands back a str — coerce to the enum.
        tier = ConsultantTier(self._require_consultant(principal.consultant_id).tier)
        fee = config.fee_for(tier)
        digest = attribution_content_hash(
            workshop_id=workshop_id,
            prospect_id=row.prospect_id,
            delivered_on=row.delivered_on,
            contracted_on=contracted_on,
            window_days=config.attribution_window_days,
            rate_ref=config.rate_ref(tier),
            fee=fee,
        )
        attribution = RecoveryFeeAttributionORM(
            owner_consultant_id=principal.consultant_id,
            workshop_id=workshop_id,
            prospect_id=row.prospect_id,
            delivered_on=row.delivered_on,
            contracted_on=contracted_on,
            window_days=config.attribution_window_days,
            rate_ref=config.rate_ref(tier),
            fee_amount_minor=fee.amount_minor,
            fee_currency=fee.currency.value,
            fee_assumption_ref=fee.assumption_register_ref,
            content_hash=digest,
        )
        self._session.add(attribution)
        self._session.flush()
        return self._to_attribution(attribution)

    def list_recovery_fee_attributions(self, principal: Principal) -> list[RecoveryFeeAttribution]:
        stmt = select(RecoveryFeeAttributionORM)
        if not principal.is_admin:
            stmt = stmt.where(
                RecoveryFeeAttributionORM.owner_consultant_id == principal.consultant_id
            )
        rows = (
            self._session.execute(stmt.order_by(RecoveryFeeAttributionORM.created_at))
            .scalars()
            .all()
        )
        result: list[RecoveryFeeAttribution] = []
        for row in rows:
            self._assert_can_access(principal, row.owner_consultant_id)  # belt and braces
            result.append(self._to_attribution(row))
        return result

    def _require_workshop(self, principal: Principal, workshop_id: UUID) -> WorkshopORM:
        row = self._session.get(WorkshopORM, workshop_id)
        if row is None:
            raise NotFoundError(f"Workshop {workshop_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        return row

    def _require_consultant(self, consultant_id: UUID) -> ConsultantORM:
        row = self._session.get(ConsultantORM, consultant_id)
        if row is None:
            raise NotFoundError(f"Consultant {consultant_id} not found.")
        return row

    def own_display_name(self, principal: Principal) -> str:
        """The caller's own full name (for their earnings statement header)."""
        return self._require_consultant(principal.consultant_id).full_name

    # ------------------------------------------------------------------ earnings (GRS-0028)
    # Governance split: an advisor VIEWS their own earnings (self-service transparency), but
    # RECORDING a commission and advancing its payment status are ADMIN/finance actions — an advisor
    # can neither set the contract value their commission derives from nor mark their own pay "paid"
    # (objective money facts are never self-attested; the ADR-0014 principle).
    _PAYMENT_ORDER = (PaymentStatus.PENDING, PaymentStatus.INVOICED, PaymentStatus.PAID)

    def _new_commission_line(
        self,
        *,
        owner_consultant_id: UUID,
        engagement_id: UUID | None,
        kind: CommissionKind,
        amount: Money,
        earned_on: date | None,
        tier: ConsultantTier | None,
        attribution: SourcingAttribution | None,
        rate_ref: str | None,
        base_value: Money | None,
        source_attribution_id: UUID | None,
        stream: CommissionStream | None = None,
        product_id: str | None = None,
        delivery_type: DeliveryType | None = None,
        contract_year: int | None = None,
        window_end: date | None = None,
        client_paid_on: date | None = None,
    ) -> CommissionLine:
        content_hash = commission_content_hash(
            owner_consultant_id=owner_consultant_id,
            engagement_id=engagement_id,
            kind=kind,
            amount=amount,
            earned_on=earned_on,
            tier=tier,
            attribution=attribution,
            rate_ref=rate_ref,
            base_value=base_value,
            source_attribution_id=source_attribution_id,
            stream=stream,
            product_id=product_id,
            delivery_type=delivery_type,
            contract_year=contract_year,
            window_end=window_end,
        )
        row = CommissionLineORM(
            owner_consultant_id=owner_consultant_id,
            engagement_id=engagement_id,
            kind=kind.value,
            amount_minor=amount.amount_minor,
            amount_currency=amount.currency.value,
            amount_assumption_ref=amount.assumption_register_ref,
            payment_status=PaymentStatus.PENDING.value,
            earned_on=earned_on,
            tier=tier.value if tier else None,
            attribution=attribution.value if attribution else None,
            rate_ref=rate_ref,
            base_value_minor=base_value.amount_minor if base_value else None,
            base_value_currency=base_value.currency.value if base_value else None,
            base_value_ref=base_value.assumption_register_ref if base_value else None,
            source_attribution_id=source_attribution_id,
            stream=stream.value if stream else None,
            product_id=product_id,
            delivery_type=delivery_type.value if delivery_type else None,
            contract_year=contract_year,
            window_end=window_end,
            client_paid_on=client_paid_on,
            content_hash=content_hash,
        )
        self._session.add(row)
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise ConflictError("This recovery fee has already been claimed.") from exc
        return self._to_commission_line(row)

    def record_product_commission(
        self,
        principal: Principal,
        *,
        advisor_id: UUID,
        engagement_id: UUID,
        base_value: Money,
        product_id: str,
        contract_year: int,
        earned_on: date,
        client_paid_on: date | None = None,
    ) -> CommissionLine:
        """Record a **Stream-A product** commission (ADR-0026) — ADMIN only. Prices Yr1/Yr2 by
        `contract_year` (£0 past the window), stamps the product provenance + `rate_ref` so a later
        config change is never retroactive, and records the window cut-off. Content-hash-sealed."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may record a commission.")
        self._require_consultant(advisor_id)
        config = load_commission_config()
        amount = compute_product_commission(base_value, product_id, contract_year, config)
        window_end = _add_months(earned_on, config.require_product(product_id).window_months)
        line = self._new_commission_line(
            owner_consultant_id=advisor_id,
            engagement_id=engagement_id,
            kind=CommissionKind.ENGAGEMENT,
            amount=amount,
            earned_on=earned_on,
            tier=None,
            attribution=None,
            rate_ref=config.product_rate_ref(product_id, contract_year),
            base_value=base_value,
            source_attribution_id=None,
            stream=CommissionStream.PRODUCT,
            product_id=product_id,
            contract_year=contract_year,
            window_end=window_end,
            client_paid_on=client_paid_on,
        )
        self._audit_commission(principal, line.id)
        return line

    def record_consultancy_commission(
        self,
        principal: Principal,
        *,
        advisor_id: UUID,
        engagement_id: UUID,
        base_value: Money,
        sourcing: SourcingAttribution,
        delivery_type: DeliveryType,
        contract_year: int,
        earned_on: date,
        client_paid_on: date | None = None,
    ) -> CommissionLine:
        """Record a **Stream-B consultancy** commission (ADR-0026) — ADMIN only. Prices the
        `delivery_type × sourcing` cell (Yr1 vs thereafter) by `contract_year`, stamps sourcing +
        delivery provenance + `rate_ref` (non-retroactive). Content-hash-sealed."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may record a commission.")
        self._require_consultant(advisor_id)
        config = load_commission_config()
        amount = compute_consultancy_commission(
            base_value, sourcing, delivery_type, contract_year, config
        )
        period = "yr1" if contract_year == 1 else "thereafter"
        line = self._new_commission_line(
            owner_consultant_id=advisor_id,
            engagement_id=engagement_id,
            kind=CommissionKind.ENGAGEMENT,
            amount=amount,
            earned_on=earned_on,
            tier=None,
            attribution=sourcing,
            rate_ref=config.consultancy_rate_ref(delivery_type, sourcing, period),
            base_value=base_value,
            source_attribution_id=None,
            stream=CommissionStream.CONSULTANCY,
            delivery_type=delivery_type,
            contract_year=contract_year,
            client_paid_on=client_paid_on,
        )
        self._audit_commission(principal, line.id)
        return line

    def _audit_commission(self, principal: Principal, line_id: UUID) -> None:
        self.record_audit(
            actor_consultant_id=principal.consultant_id,
            event_type=AuditEventType.COMMISSION_RECORDED,
            resource_type="commission_line",
            resource_id=line_id,
            now=datetime.now(UTC),
        )

    def claim_recovery_fee(
        self, principal: Principal, *, attribution_id: UUID, earned_on: date
    ) -> CommissionLine:
        """Turn an eligible recovery-fee attribution into a claimed commission line — ADMIN only.
        Idempotent per attribution: a second claim of the same fee is refused (ConflictError)."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may claim a recovery fee.")
        attr = self._session.get(RecoveryFeeAttributionORM, attribution_id)
        if attr is None:
            raise NotFoundError(f"Recovery-fee attribution {attribution_id} not found.")
        amount = Money(
            amount_minor=attr.fee_amount_minor,
            currency=Currency(attr.fee_currency),
            assumption_register_ref=attr.fee_assumption_ref,
        )
        return self._new_commission_line(
            owner_consultant_id=attr.owner_consultant_id,
            engagement_id=None,
            kind=CommissionKind.WORKSHOP_RECOVERY_FEE,
            amount=amount,
            earned_on=earned_on,
            tier=None,
            attribution=None,
            rate_ref=attr.rate_ref,
            base_value=None,
            source_attribution_id=attribution_id,
        )

    def advance_commission_payment(
        self, principal: Principal, line_id: UUID, *, to_status: PaymentStatus
    ) -> CommissionLine:
        """Advance a commission line's payment status — ADMIN only. Forward-only along
        pending → invoiced → paid; a backward move or a skip is refused (ConflictError). The sealed
        financial figures are untouched (payment_status is not part of the content hash)."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may change a commission's payment status.")
        row = self._session.get(CommissionLineORM, line_id)
        if row is None:
            raise NotFoundError(f"Commission line {line_id} not found.")
        current = PaymentStatus(row.payment_status)
        if self._PAYMENT_ORDER.index(to_status) != self._PAYMENT_ORDER.index(current) + 1:
            raise ConflictError(
                f"Illegal payment transition {current.value} → {to_status.value}: status advances "
                f"one step forward only (pending → invoiced → paid)."
            )
        # Pay-when-paid (ADR-0026): a line cannot reach `paid` until the client cash it derives from
        # has been received and retained — `client_paid_on` must be set first.
        if to_status is PaymentStatus.PAID and row.client_paid_on is None:
            raise ConflictError(
                "Pay-when-paid: cannot mark this commission paid until the client cash it derives "
                "from is recorded (client_paid_on is unset)."
            )
        row.payment_status = to_status.value
        self._session.add(row)
        self._session.flush()
        return self._to_commission_line(row)

    def record_client_paid(
        self, principal: Principal, line_id: UUID, *, client_paid_on: date
    ) -> CommissionLine:
        """Record the date the client cash a commission derives from was received — ADMIN only
        (ADR-0026 pay-when-paid). `client_paid_on` is OUTSIDE the content-hash seal (a lifecycle
        precondition, like payment_status), so this does not violate immutability; the sealed
        financial figures are untouched. It is the gate that then permits advancing to `paid`."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may record client payment.")
        row = self._session.get(CommissionLineORM, line_id)
        if row is None:
            raise NotFoundError(f"Commission line {line_id} not found.")
        row.client_paid_on = client_paid_on
        self._session.add(row)
        self._session.flush()
        return self._to_commission_line(row)

    def list_commission_lines(self, principal: Principal) -> list[CommissionLine]:
        """The caller's OWN commission lines — strictly self-scoped (earnings transparency is
        self-service; the cross-advisor aggregate is Holy Corner scope, not this ticket)."""
        rows = (
            self._session.execute(
                select(CommissionLineORM)
                .where(CommissionLineORM.owner_consultant_id == principal.consultant_id)
                .order_by(CommissionLineORM.created_at)
            )
            .scalars()
            .all()
        )
        return [self._to_commission_line(r) for r in rows]

    def earnings_summary(self, principal: Principal, *, now: datetime) -> EarningsSummary:
        """The caller's own earnings roll-up (self only). Totals are summed within the config
        currency; YTD counts lines earned in the current calendar year."""
        lines = self.list_commission_lines(principal)
        currency = load_commission_config().currency
        totals = {status: 0 for status in PaymentStatus}
        ytd = 0
        for line in lines:
            if line.amount.currency is not currency:
                raise ConflictError(
                    f"Commission line {line.id} is in {line.amount.currency.value}, not the "
                    f"{currency.value} earnings currency — refusing to sum across currencies."
                )
            totals[line.payment_status] += line.amount.amount_minor
            earned_year = line.earned_on.year if line.earned_on else line.created_at.year
            if earned_year == now.year:
                ytd += line.amount.amount_minor

        def money(minor: int, ref: str) -> Money:
            return Money(amount_minor=minor, currency=currency, assumption_register_ref=ref)

        pending = totals[PaymentStatus.PENDING]
        invoiced = totals[PaymentStatus.INVOICED]
        return EarningsSummary(
            owner_consultant_id=principal.consultant_id,
            currency=currency,
            ytd_earned=money(ytd, "earnings-summary:ytd"),
            pending=money(pending, "earnings-summary:pending"),
            invoiced=money(invoiced, "earnings-summary:invoiced"),
            paid=money(totals[PaymentStatus.PAID], "earnings-summary:paid"),
            projected_unpaid=money(pending + invoiced, "earnings-summary:projected-unpaid"),
            line_count=len(lines),
        )

    def earnings_timeline(self, principal: Principal, *, now: datetime) -> EarningsTimeline:
        """The caller's earnings over time + the two v7 stream totals (GRS-0133). Aggregates the
        already-computed commission lines in the Money domain — no rate, rounding, or lifecycle
        change. Self only, single currency (a cross-currency line refuses to sum)."""
        lines = self.list_commission_lines(principal)
        currency = load_commission_config().currency
        by_period: dict[str, int] = {}
        stream_totals = {CommissionStream.PRODUCT: 0, CommissionStream.CONSULTANCY: 0}
        for line in lines:
            if line.amount.currency is not currency:
                raise ConflictError(
                    f"Commission line {line.id} is in {line.amount.currency.value}, not the "
                    f"{currency.value} earnings currency — refusing to sum across currencies."
                )
            earned = line.earned_on if line.earned_on else line.created_at.date()
            period = f"{earned.year:04d}-{earned.month:02d}"
            by_period[period] = by_period.get(period, 0) + line.amount.amount_minor
            if line.stream is not None:
                stream_totals[line.stream] += line.amount.amount_minor

        def money(minor: int, ref: str) -> Money:
            return Money(amount_minor=minor, currency=currency, assumption_register_ref=ref)

        points: list[EarningsTimelinePoint] = []
        cumulative = 0
        for period in sorted(by_period):
            cumulative += by_period[period]
            points.append(
                EarningsTimelinePoint(
                    period=period,
                    earned=money(by_period[period], f"earnings-timeline:{period}:earned"),
                    cumulative=money(cumulative, f"earnings-timeline:{period}:cumulative"),
                )
            )
        return EarningsTimeline(
            owner_consultant_id=principal.consultant_id,
            currency=currency,
            points=tuple(points),
            stream_product=money(
                stream_totals[CommissionStream.PRODUCT], "earnings-timeline:stream-product"
            ),
            stream_consultancy=money(
                stream_totals[CommissionStream.CONSULTANCY], "earnings-timeline:stream-consultancy"
            ),
        )

    @staticmethod
    def _to_commission_line(row: CommissionLineORM) -> CommissionLine:
        base_value = (
            Money(
                amount_minor=row.base_value_minor,
                currency=Currency(row.base_value_currency),
                assumption_register_ref=row.base_value_ref,
            )
            if row.base_value_minor is not None
            and row.base_value_currency is not None
            and row.base_value_ref is not None
            else None
        )
        return CommissionLine(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            engagement_id=row.engagement_id,
            kind=CommissionKind(row.kind),
            amount=Money(
                amount_minor=row.amount_minor,
                currency=Currency(row.amount_currency),
                assumption_register_ref=row.amount_assumption_ref,
            ),
            payment_status=PaymentStatus(row.payment_status),
            earned_on=row.earned_on,
            tier=ConsultantTier(row.tier) if row.tier else None,
            attribution=SourcingAttribution(row.attribution) if row.attribution else None,
            rate_ref=row.rate_ref,
            base_value=base_value,
            source_attribution_id=row.source_attribution_id,
            stream=CommissionStream(row.stream) if row.stream else None,
            product_id=row.product_id,
            delivery_type=DeliveryType(row.delivery_type) if row.delivery_type else None,
            contract_year=row.contract_year,
            window_end=row.window_end,
            client_paid_on=row.client_paid_on,
            content_hash=row.content_hash,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ------------------------------------------- Path B: meeting transcripts (GRS-0029, SCOPED)
    def ingest_pasted_transcript(
        self,
        principal: Principal,
        *,
        text: str,
        source_filename: str,
        cipher: TranscriptCipher,
        engagement_id: UUID | None = None,
        retention_until: date | None = None,
    ) -> MeetingTranscript:
        """Store a pasted transcript — no transcription needed. Encrypted at rest (plaintext never
        hits the DB); owned by the caller."""
        return self._store_transcript(
            principal,
            text=text,
            source_kind=MediaKind.TRANSCRIPT_TEXT,
            source_filename=source_filename,
            transcriber_ref="pasted",
            cipher=cipher,
            engagement_id=engagement_id,
            retention_until=retention_until,
        )

    def ingest_media(
        self,
        principal: Principal,
        *,
        media: bytes,
        source_filename: str,
        content_type: str,
        source_kind: MediaKind,
        transcriber: Transcriber,
        scanner: MediaScanner,
        cipher: TranscriptCipher,
        engagement_id: UUID | None = None,
        retention_until: date | None = None,
    ) -> MeetingTranscript:
        """Scan → transcribe → store an uploaded audio/video file. The scanner runs FIRST,
        by raising (nothing is transcribed or stored on a refusal); the transcript is then encrypted
        at rest. The transcriber and scanner are injected ports (swappable by config)."""
        # Empty media is refused at the ingest boundary, so the guarantee holds regardless of which
        # transcriber is injected (a provider without its own empty-guard cannot store a blank).
        if not media:
            raise TranscriptionError(f"Refusing to ingest empty media ({source_filename}).")
        scanner.scan(media, filename=source_filename)  # raises MediaThreatError to refuse
        text = transcriber.transcribe(media, filename=source_filename, content_type=content_type)
        return self._store_transcript(
            principal,
            text=text,
            source_kind=source_kind,
            source_filename=source_filename,
            transcriber_ref=transcriber.version,
            cipher=cipher,
            engagement_id=engagement_id,
            retention_until=retention_until,
        )

    def _store_transcript(
        self,
        principal: Principal,
        *,
        text: str,
        source_kind: MediaKind,
        source_filename: str,
        transcriber_ref: str,
        cipher: TranscriptCipher,
        engagement_id: UUID | None,
        retention_until: date | None,
    ) -> MeetingTranscript:
        # A supplied engagement must exist and belong to the caller — otherwise a transcript could
        # be attached to another consultant's (or a non-existent) engagement, a dangling/foreign
        # reference. Cross-owner or missing → refused (NotFound/Scope → 404), like every other link.
        if engagement_id is not None:
            self._require_engagement(principal, engagement_id)
        row = MeetingTranscriptORM(
            owner_consultant_id=principal.consultant_id,
            engagement_id=engagement_id,
            source_kind=source_kind.value,
            source_filename=source_filename,
            text_ciphertext=cipher.encrypt(text),
            transcriber_ref=transcriber_ref,
            retention_until=retention_until,
        )
        self._session.add(row)
        self._session.flush()
        return self._to_meeting_transcript(row, cipher)

    def list_transcripts(
        self, principal: Principal, *, cipher: TranscriptCipher
    ) -> list[MeetingTranscript]:
        """The caller's own transcripts (an admin sees all), text decrypted for the reader."""
        stmt = select(MeetingTranscriptORM)
        if not principal.is_admin:
            stmt = stmt.where(MeetingTranscriptORM.owner_consultant_id == principal.consultant_id)
        rows = self._session.execute(stmt.order_by(MeetingTranscriptORM.created_at)).scalars().all()
        return [self._to_meeting_transcript(r, cipher) for r in rows]

    def get_transcript(
        self, principal: Principal, transcript_id: UUID, *, cipher: TranscriptCipher
    ) -> MeetingTranscript:
        """A single transcript, with its text decrypted — the owner's (or an admin's). A cross-owner
        read is refused (ScopeViolationError → 404)."""
        row = self._session.get(MeetingTranscriptORM, transcript_id)
        if row is None:
            raise NotFoundError(f"Transcript {transcript_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        return self._to_meeting_transcript(row, cipher)

    @staticmethod
    def _to_meeting_transcript(
        row: MeetingTranscriptORM, cipher: TranscriptCipher
    ) -> MeetingTranscript:
        return MeetingTranscript(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            engagement_id=row.engagement_id,
            source_kind=MediaKind(row.source_kind),
            source_filename=row.source_filename,
            text=cipher.decrypt(row.text_ciphertext),
            transcriber_ref=row.transcriber_ref,
            retention_until=row.retention_until,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ------------------------------------------- Path B: extraction → review (GRS-0030, SCOPED, #8)
    def propose_extraction(
        self,
        principal: Principal,
        *,
        assessment_id: UUID,
        transcript_id: UUID,
        extractor: Extractor,
        cipher: TranscriptCipher,
    ) -> Extraction:
        """Extract one of the caller's transcripts into a PROPOSED assessment document — a GATED
        proposal (#8). The proposed document lives on the extraction, NOT the assessment, so nothing
        unconfirmed can reach the engine. Extracted evidence grades are capped (E1 default, never
        above E2 without an artifact). Per-field provenance is persisted."""
        assessment = self._require_assessment(principal, assessment_id)  # own + exists
        transcript = self.get_transcript(principal, transcript_id, cipher=cipher)  # own + decrypts
        result = extractor.extract(transcript.text, subject=assessment.subject)
        proposed = _cap_extraction_evidence(result.proposed_document)
        row = ExtractionORM(
            owner_consultant_id=principal.consultant_id,
            assessment_id=assessment_id,
            transcript_id=transcript_id,
            status=ExtractionStatus.PROPOSED.value,
            proposed_document_json=proposed.model_dump_json(),
            gaps_json=json.dumps(list(result.gaps)),
            extractor_version=extractor.version,
        )
        self._session.add(row)
        self._session.flush()
        for spec in result.fields:
            self._session.add(
                FieldProvenanceORM(
                    owner_consultant_id=principal.consultant_id,
                    extraction_id=row.id,
                    transcript_id=transcript_id,
                    field_ref=spec.field_ref,
                    confidence=spec.confidence.value,
                    span_start=spec.span_start,
                    span_end=spec.span_end,
                    accepted=False,
                )
            )
        self._session.flush()
        return self._to_extraction(row)

    def confirm_extraction(
        self,
        principal: Principal,
        extraction_id: UUID,
        *,
        now: datetime,
        corrected_document: AssessmentDocument | None = None,
    ) -> Extraction:
        """Confirm an extraction: apply the (optionally corrected) document to the assessment via
        the SAME Path A save path (`update_assessment`), so confirmed Path B data is indistinct
        from manual entry downstream — the byte-identical-scoring guarantee. Marks the extraction
        CONFIRMED and every field accepted. Refused once confirmed (ConflictError)."""
        row = self._session.get(ExtractionORM, extraction_id)
        if row is None:
            raise NotFoundError(f"Extraction {extraction_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        if row.status != ExtractionStatus.PROPOSED.value:
            raise ConflictError(f"Extraction {extraction_id} is already confirmed.")
        document = corrected_document or AssessmentDocument.model_validate_json(
            row.proposed_document_json
        )
        document = _cap_extraction_evidence(document)  # a correction is capped the same way
        # THE convergence: the confirmed document enters the assessment through the identical Path A
        # path, so a scoring run over it is byte-identical to the same data typed into the wizard.
        self.update_assessment(principal, row.assessment_id, document=document)
        row.status = ExtractionStatus.CONFIRMED.value
        row.confirmed_at = now
        self._session.add(row)
        for prov in self._session.execute(
            select(FieldProvenanceORM).where(FieldProvenanceORM.extraction_id == extraction_id)
        ).scalars():
            prov.accepted = True
            self._session.add(prov)
        self._session.flush()
        return self._to_extraction(row)

    def get_extraction(self, principal: Principal, extraction_id: UUID) -> Extraction:
        row = self._session.get(ExtractionORM, extraction_id)
        if row is None:
            raise NotFoundError(f"Extraction {extraction_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        return self._to_extraction(row)

    def list_field_provenance(
        self, principal: Principal, extraction_id: UUID
    ) -> list[FieldProvenance]:
        """The per-field audit trail for an extraction — the caller's own."""
        self.get_extraction(principal, extraction_id)  # own + exists (raises on foreign)
        rows = (
            self._session.execute(
                select(FieldProvenanceORM)
                .where(FieldProvenanceORM.extraction_id == extraction_id)
                .order_by(FieldProvenanceORM.created_at)
            )
            .scalars()
            .all()
        )
        return [self._to_field_provenance(r) for r in rows]

    @staticmethod
    def _to_extraction(row: ExtractionORM) -> Extraction:
        return Extraction(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            assessment_id=row.assessment_id,
            transcript_id=row.transcript_id,
            status=ExtractionStatus(row.status),
            proposed_document=AssessmentDocument.model_validate_json(row.proposed_document_json),
            gaps=tuple(json.loads(row.gaps_json)),
            extractor_version=row.extractor_version,
            confirmed_at=row.confirmed_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_field_provenance(row: FieldProvenanceORM) -> FieldProvenance:
        return FieldProvenance(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            extraction_id=row.extraction_id,
            transcript_id=row.transcript_id,
            field_ref=row.field_ref,
            confidence=ExtractionConfidence(row.confidence),
            span_start=row.span_start,
            span_end=row.span_end,
            accepted=row.accepted,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ------------------------------------------------- prediction register + benchmark (GRS-0031)
    def register_predictions(
        self,
        principal: Principal,
        *,
        scoring_run_id: UUID,
        specs: Sequence[PredictionSpec],
        horizon_months: int,
        probability: float,
        follow_up_due: date,
    ) -> list[Prediction]:
        """Pre-register one prediction per lever against an immutable scoring run — the
        falsifiability record. The run must be the caller's own (scoped)."""
        self.get_scoring_run(principal, scoring_run_id)  # own + exists (raises otherwise)
        created: list[Prediction] = []
        for spec in specs:
            row = PredictionORM(
                owner_consultant_id=principal.consultant_id,
                scoring_run_id=scoring_run_id,
                lever=spec.lever.value,
                predicted_delta_minor=spec.predicted_delta.amount_minor,
                predicted_delta_currency=spec.predicted_delta.currency.value,
                predicted_delta_ref=spec.predicted_delta.assumption_register_ref,
                horizon_months=horizon_months,
                probability=probability,
                follow_up_due=follow_up_due,
                outcome=PredictionOutcome.PENDING.value,
            )
            self._session.add(row)
            self._session.flush()
            created.append(self._to_prediction(row))
        return created

    def list_predictions(self, principal: Principal) -> list[Prediction]:
        """The caller's own predictions."""
        rows = (
            self._session.execute(
                select(PredictionORM)
                .where(PredictionORM.owner_consultant_id == principal.consultant_id)
                .order_by(PredictionORM.created_at)
            )
            .scalars()
            .all()
        )
        return [self._to_prediction(r) for r in rows]

    def list_due_follow_ups(self, principal: Principal, *, now: datetime) -> list[Prediction]:
        """The caller's predictions whose follow-up is due (follow_up_due ≤ today) and still
        PENDING — the re-contacts to chase for realised value."""
        rows = (
            self._session.execute(
                select(PredictionORM)
                .where(
                    PredictionORM.owner_consultant_id == principal.consultant_id,
                    PredictionORM.outcome == PredictionOutcome.PENDING.value,
                    PredictionORM.follow_up_due <= now.date(),
                )
                .order_by(PredictionORM.follow_up_due)
            )
            .scalars()
            .all()
        )
        return [self._to_prediction(r) for r in rows]

    def get_prediction(self, principal: Principal, prediction_id: UUID) -> Prediction:
        row = self._session.get(PredictionORM, prediction_id)
        if row is None:
            raise NotFoundError(f"Prediction {prediction_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        return self._to_prediction(row)

    def record_realised_value(
        self, principal: Principal, prediction_id: UUID, *, realised_delta: Money, now: datetime
    ) -> Prediction:
        """Record a follow-up's realised value and score the prediction — a directional hit/miss and
        a Brier score. Single-shot: refused once already scored."""
        row = self._session.get(PredictionORM, prediction_id)
        if row is None:
            raise NotFoundError(f"Prediction {prediction_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        if row.outcome != PredictionOutcome.PENDING.value:
            raise ConflictError(f"Prediction {prediction_id} has already been scored.")
        predicted = Money(
            amount_minor=row.predicted_delta_minor,
            currency=Currency(row.predicted_delta_currency),
            assumption_register_ref=row.predicted_delta_ref,
        )
        outcome, brier = score_prediction(
            predicted_delta=predicted, realised_delta=realised_delta, probability=row.probability
        )
        row.outcome = outcome.value
        row.realised_delta_minor = realised_delta.amount_minor
        row.realised_delta_currency = realised_delta.currency.value
        row.realised_delta_ref = realised_delta.assumption_register_ref
        row.brier_score = brier
        row.scored_at = now
        self._session.add(row)
        self._session.flush()
        return self._to_prediction(row)

    def ingest_benchmark(
        self,
        principal: Principal,
        scoring_run_id: UUID,
        *,
        sector: BenchmarkSector | None,
        now: datetime,
    ) -> BenchmarkRow:
        """Ingest a FINALISED scoring run into the anonymised benchmark population. The row is
        de-identified by construction — only the score, uncertainty, versions, and a non-identifying
        sector are copied; no owner, assessment id, run id, or client detail crosses over."""
        run = self.get_scoring_run(principal, scoring_run_id)  # own + exists
        if not run.finalised:
            raise ConflictError("Only a finalised scoring run may enter the benchmark population.")
        if run.v_index is None:
            raise ConflictError("Scoring run has no V index to benchmark.")
        # Non-production (demo/sandbox) records are segregated — they never enter the benchmark
        # population (ADR-0029). A sandbox tester's throwaway score is not a peer data point. We
        # exclude only when the record is CONFIRMED non-production; an unfindable assessment is not
        # a sandbox record we are protecting against, so it does not block (never a silent scoring
        # fallback — this is a benchmark-eligibility check).
        try:
            provenance = self.get_assessment(principal, run.assessment_id).provenance
        except NotFoundError:
            provenance = RecordProvenance.PRODUCTION
        if provenance is not RecordProvenance.PRODUCTION:
            raise ConflictError(
                f"A {provenance.value} record is non-production and cannot enter the benchmark "
                f"population (ADR-0029)."
            )
        row = BenchmarkRowORM(
            v_index=run.v_index,
            v_p10=run.v_p10,
            v_p90=run.v_p90,
            uncertainty_rating=run.uncertainty_rating.value if run.uncertainty_rating else None,
            methodology_version=run.methodology_version,
            coefficient_version=run.coefficient_version,
            sector=sector.value if sector else None,
            ingested_at=now,
        )
        self._session.add(row)
        self._session.flush()
        return self._to_benchmark_row(row)

    def list_benchmark_rows(
        self, *, limit: int | None = None, offset: int = 0
    ) -> list[BenchmarkRow]:
        """The anonymised benchmark population — org-wide and de-identified, so not owner-scoped.
        Paginated (capped) — the population grows without bound as runs are ingested."""
        rows = (
            self._session.execute(
                select(BenchmarkRowORM)
                .order_by(BenchmarkRowORM.ingested_at)
                .limit(_clamp_limit(limit))
                .offset(max(0, offset))
            )
            .scalars()
            .all()
        )
        return [self._to_benchmark_row(r) for r in rows]

    @staticmethod
    def _to_prediction(row: PredictionORM) -> Prediction:
        from bcap_contracts.value import LeverKind

        realised = (
            Money(
                amount_minor=row.realised_delta_minor,
                currency=Currency(row.realised_delta_currency),
                assumption_register_ref=row.realised_delta_ref,
            )
            if row.realised_delta_minor is not None
            and row.realised_delta_currency is not None
            and row.realised_delta_ref is not None
            else None
        )
        return Prediction(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            scoring_run_id=row.scoring_run_id,
            lever=LeverKind(row.lever),
            predicted_delta=Money(
                amount_minor=row.predicted_delta_minor,
                currency=Currency(row.predicted_delta_currency),
                assumption_register_ref=row.predicted_delta_ref,
            ),
            horizon_months=row.horizon_months,
            probability=row.probability,
            follow_up_due=row.follow_up_due,
            outcome=PredictionOutcome(row.outcome),
            realised_delta=realised,
            brier_score=row.brier_score,
            scored_at=row.scored_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_benchmark_row(row: BenchmarkRowORM) -> BenchmarkRow:
        return BenchmarkRow(
            id=row.id,
            v_index=row.v_index,
            v_p10=row.v_p10,
            v_p90=row.v_p90,
            uncertainty_rating=UncertaintyRating(row.uncertainty_rating)
            if row.uncertainty_rating
            else None,
            methodology_version=row.methodology_version,
            coefficient_version=row.coefficient_version,
            sector=BenchmarkSector(row.sector) if row.sector else None,
            ingested_at=row.ingested_at,
        )

    # ------------------------------------------------------ C benchmark set (ADR-0023 / GRS-0084)
    def propose_c_benchmark_row(
        self,
        principal: Principal,
        *,
        peer_name: str,
        profile_key: str,
        c_index: float,
        module_scores: dict[str, float],
        methodology_version: str,
        coefficient_version: str,
        source_ref: str | None,
        now: datetime,
    ) -> CBenchmarkRow:
        """Propose a C benchmark row for a named public-app peer (ADR-0023). The row is created
        UNAPPROVED (ADR-0009 / CLAUDE.md #8: AI/consultant proposes, a human approves) — it is not
        live for comparison until :meth:`approve_c_benchmark_row` records a sign-off. Any consultant
        may propose; the peer set is a shared org-wide reference (peers are public apps, not client
        data)."""
        row = CBenchmarkRowORM(
            peer_name=peer_name,
            profile_key=profile_key,
            c_index=c_index,
            module_scores=dict(module_scores),
            methodology_version=methodology_version,
            coefficient_version=coefficient_version,
            source_ref=source_ref,
            approved=False,
            approved_by=None,
            approved_at=None,
            ingested_at=now,
        )
        self._session.add(row)
        self._session.flush()
        return self._to_c_benchmark_row(row)

    def approve_c_benchmark_row(
        self, principal: Principal, row_id: UUID, *, now: datetime
    ) -> CBenchmarkRow:
        """Record the ADR-0009 human approval that makes a proposed row live. Idempotent-safe:
        re-approving an approved row keeps the ORIGINAL approver/timestamp (the recorded first
        sign-off is the auditable fact, never silently overwritten)."""
        row = self._session.get(CBenchmarkRowORM, row_id)
        if row is None:
            raise NotFoundError(f"C benchmark row {row_id} not found.")
        if not row.approved:
            row.approved = True
            row.approved_by = principal.consultant_id
            row.approved_at = now
            self._session.flush()
        return self._to_c_benchmark_row(row)

    def list_c_benchmark_rows(
        self,
        *,
        approved_only: bool = True,
        profile_key: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[CBenchmarkRow]:
        """The C benchmark peer set — a shared org-wide reference (not owner-scoped). By default
        only APPROVED rows (the live comparison set, ADR-0009); pass ``approved_only=False`` to
        include pending proposals (e.g. an approval queue). Optionally filtered to one operating-
        model profile so a subject only compares against same-profile peers."""
        stmt = select(CBenchmarkRowORM)
        if approved_only:
            stmt = stmt.where(CBenchmarkRowORM.approved.is_(True))
        if profile_key is not None:
            stmt = stmt.where(CBenchmarkRowORM.profile_key == profile_key)
        stmt = (
            stmt.order_by(CBenchmarkRowORM.c_index.desc())
            .limit(_clamp_limit(limit))
            .offset(max(0, offset))
        )
        rows = self._session.execute(stmt).scalars().all()
        return [self._to_c_benchmark_row(r) for r in rows]

    @staticmethod
    def _to_c_benchmark_row(row: CBenchmarkRowORM) -> CBenchmarkRow:
        return CBenchmarkRow(
            id=row.id,
            peer_name=row.peer_name,
            profile_key=row.profile_key,
            c_index=row.c_index,
            module_scores=dict(row.module_scores or {}),
            methodology_version=row.methodology_version,
            coefficient_version=row.coefficient_version,
            source_ref=row.source_ref,
            approved=row.approved,
            approved_by=row.approved_by,
            approved_at=row.approved_at,
            ingested_at=row.ingested_at,
        )

    # ---------------------------------------------- audit log + GDPR compliance (GRS-0032)
    def record_audit(
        self,
        *,
        actor_consultant_id: UUID | None,
        event_type: AuditEventType,
        now: datetime,
        resource_type: str | None = None,
        resource_id: UUID | None = None,
        detail: str | None = None,
        acting_admin_id: UUID | None = None,
    ) -> None:
        """Write one APPEND-ONLY audit event. Never updated or deleted. `detail` must carry no
        secret (no tokens, no passwords, no plaintext transcript).

        `acting_admin_id` is set when the actor is an admin acting as another consultant
        (GRS-0208). It is appended to the detail rather than replacing the actor, because the record
        has to say BOTH things: the work is the subject's, and a named admin did it. Dropping either
        half is how an audit log stops answering the question it exists for.
        """
        if acting_admin_id is not None:
            note = (
                f"acting-as: performed by admin {acting_admin_id} "
                f"on behalf of {actor_consultant_id}"
            )
            detail = f"{detail} | {note}" if detail else note
        self._session.add(
            AuditEventORM(
                actor_consultant_id=actor_consultant_id,
                event_type=event_type.value,
                resource_type=resource_type,
                resource_id=resource_id,
                detail=detail,
                at=now,
            )
        )
        self._session.flush()

    def list_consultants_for_act_as(self, principal: Principal) -> list[Consultant]:
        """Everyone an admin could act as (GRS-0208). ADMIN only.

        Deliberately narrow, and named for its one purpose rather than as a general directory: it
        exists so the act-as picker has something to show, and a general `list_consultants` would be
        a roster endpoint nobody asked for on a product whose whole scoping discipline is that
        advisors do not see each other.

        Excludes the caller (acting as yourself is refused anyway) and inactive accounts, so the
        picker cannot offer a choice the gate will reject.
        """
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may list consultants to act as.")
        rows = (
            self._session.execute(
                select(ConsultantORM)
                .where(
                    ConsultantORM.id != principal.consultant_id,
                    ConsultantORM.is_active.is_(True),
                )
                .order_by(ConsultantORM.full_name)
            )
            .scalars()
            .all()
        )
        return [self._to_stored_consultant(r).to_contract() for r in rows]

    # ------------------------------------------------------------------ act-as (GRS-0208)

    def begin_act_as(
        self,
        principal: Principal,
        subject_id: UUID,
        *,
        now: datetime,
        founder_reviewer_email: str,
    ) -> Principal:
        """Open a session scoped to another consultant, and return the principal to run it under.

        Three rules, all enforced here rather than in a router, because scoping lives in this layer
        (non-negotiable #9):

        1. **Only an admin may start it.** Not a committee member, not a founder who is not also an
           admin, and never a consultant.
        2. **The returned principal IS the subject** — their id, their role, their founder status.
           It is not an admin principal with a note attached, which is what would make act-as a way
           to see more rather than a way to see exactly what one advisor sees.
        3. **An admin already acting as someone may not chain** to a third consultant without
           ending first. Chaining would make the audit trail ambiguous about who authorised what.
        """
        if not principal.is_admin:
            raise ScopeViolationError(
                "Only an admin may act as another consultant (GRS-0208). Data scoping is absolute "
                "(CLAUDE.md non-negotiable #9)."
            )
        if principal.is_acting_as:
            raise ConflictError(
                "Already acting as another consultant. End that session before starting a new one "
                "— chained act-as makes the audit trail ambiguous about who authorised what."
            )
        subject = self._session.get(ConsultantORM, subject_id)
        if subject is None:
            raise NotFoundError(f"Consultant {subject_id} not found.")
        if subject.id == principal.consultant_id:
            raise ConflictError("You are already yourself; acting as yourself would record a lie.")
        self.record_audit(
            actor_consultant_id=principal.consultant_id,
            event_type=AuditEventType.ACT_AS_STARTED,
            now=now,
            resource_type="consultant",
            resource_id=subject.id,
            detail=f"admin {principal.consultant_id} began acting as {subject.email}",
        )
        return Principal(
            consultant_id=subject.id,
            role=Role(subject.role),
            # The SUBJECT's founder status, not the admin's. An admin acting as an advisor must not
            # carry a claim that advisor does not have, or "see exactly what they see" is false at
            # precisely the gate that matters most (ADR-0041).
            is_founder=subject.email.strip().lower() == founder_reviewer_email.strip().lower(),
            acting_admin_id=principal.consultant_id,
        )

    def end_act_as(self, principal: Principal, *, now: datetime) -> None:
        """Close an act-as session. Recorded, so the log shows a bounded interval rather than an
        open-ended one — 'when did they stop' is as much a question as 'when did they start'."""
        if not principal.is_acting_as:
            raise ConflictError("Not currently acting as another consultant.")
        self.record_audit(
            actor_consultant_id=principal.acting_admin_id,
            event_type=AuditEventType.ACT_AS_ENDED,
            now=now,
            resource_type="consultant",
            resource_id=principal.consultant_id,
            detail=f"admin {principal.acting_admin_id} stopped acting as {principal.consultant_id}",
        )

    def list_audit_events(
        self, principal: Principal, *, limit: int | None = None, offset: int = 0
    ) -> list[AuditEvent]:
        """The audit log — ADMIN only (compliance). Newest first, paginated (capped) — the log is
        append-only and org-wide, so it must never be returned unbounded."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may read the audit log.")
        rows = (
            self._session.execute(
                select(AuditEventORM)
                .order_by(AuditEventORM.at.desc(), AuditEventORM.id.desc())
                .limit(_clamp_limit(limit))
                .offset(max(0, offset))
            )
            .scalars()
            .all()
        )
        return [
            AuditEvent(
                id=r.id,
                owner_consultant_id=r.actor_consultant_id or _SYSTEM_ACTOR,
                event_type=AuditEventType(r.event_type),
                resource_type=r.resource_type,
                resource_id=r.resource_id,
                detail=r.detail,
                at=r.at,
                created_at=r.created_at,
                updated_at=r.updated_at,
            )
            for r in rows
        ]

    def _registry_contacts_for_email(self, email: str) -> list[RegistryContactORM]:
        """Imported registry rows belonging to one data subject, matched case-insensitively on
        email. An empty email never matches, so an anonymised consultant cannot sweep up the rows
        of every contact whose email is unset."""
        if not email.strip():
            return []
        stmt = select(RegistryContactORM).where(
            func.lower(RegistryContactORM.email) == email.strip().lower()
        )
        return list(self._session.execute(stmt).scalars())

    def _require_self_or_admin(self, principal: Principal, subject_id: UUID) -> None:
        if not (principal.is_admin or subject_id == principal.consultant_id):
            raise ScopeViolationError("You may export or delete only your own personal data.")

    def export_personal_data(
        self, principal: Principal, subject_id: UUID, *, now: datetime
    ) -> PersonalDataExport:
        """The GDPR subject-access bundle — every record the platform holds about `subject_id`, self
        or admin. Reflection over the ORM registry means EVERY owned table is covered (present and
        future) — no manual list to drift. The password hash and raw ciphertext are redacted."""
        self._require_self_or_admin(principal, subject_id)
        records: dict[str, list[dict]] = {}
        consultant = self._require_consultant(subject_id)
        records["consultant"] = [_row_to_dict(consultant, redact=frozenset({"hashed_password"}))]
        for orm in _owned_orm_classes():
            rows = (
                self._session.execute(select(orm).where(orm.owner_consultant_id == subject_id))
                .scalars()
                .all()
            )
            records[orm.__tablename__] = [_row_to_dict(r) for r in rows]
        # Invitations are not owner-scoped but carry the subject's PII (their inbound invite holds
        # their email; outbound invites carry their id) — include them so the SAR is complete.
        invitations = (
            self._session.execute(
                select(InvitationORM).where(
                    (InvitationORM.email == consultant.email)
                    | (InvitationORM.invited_by_consultant_id == subject_id)
                )
            )
            .scalars()
            .all()
        )
        records["invitations"] = [
            _row_to_dict(r, redact=frozenset({"token_hash"})) for r in invitations
        ]
        # Registry contacts are imported business-contact PII and are NOT owner-scoped, so the loop
        # above never reaches them (GRS-0193 §7). A consultant who also appears in an imported
        # roster — an analyst who later joins the network — is the same data subject, matched on
        # email, and their SAR must include those rows.
        records["registry_contacts"] = [
            _row_to_dict(r) for r in self._registry_contacts_for_email(consultant.email)
        ]
        self.record_audit(
            actor_consultant_id=principal.consultant_id,
            event_type=AuditEventType.GDPR_EXPORT,
            resource_type="consultant",
            resource_id=subject_id,
            now=now,
        )
        return PersonalDataExport(
            subject_consultant_id=subject_id, generated_at=now, records=records
        )

    def delete_personal_data(
        self, principal: Principal, subject_id: UUID, *, now: datetime
    ) -> dict[str, int]:
        """GDPR erasure — self or admin. Deletes every owned row EXCEPT scoring runs, and anonymises
        the consultant (PII stripped, id kept). Scoring runs are immutable (#6): NOT deleted but
        become de-identified — their now-anonymised owner id is an opaque key with no PII. The
        audit log survives (compliance). Deletion runs children-before-parents (FK-safe)."""
        self._require_self_or_admin(principal, subject_id)
        counts: dict[str, int] = {}

        # CROSS-OWNER FK children first. Some tables are owned by ANOTHER consultant yet
        # FK-reference a row the SUBJECT owns: a rater's module draft on the subject's assessment,
        # or an advisor's arena session on the subject's authored scenario. The owner-scoped loop
        # below never touches them, so deleting the subject's parent row would orphan the FK and (on
        # Postgres) abort the whole erasure. Delete them by their PARENT's ownership up front.
        subject_assessments = select(AssessmentORM.id).where(
            AssessmentORM.owner_consultant_id == subject_id
        )
        counts["module_rating_drafts"] = (
            getattr(
                self._session.execute(
                    delete(ModuleRatingDraftORM).where(
                        ModuleRatingDraftORM.assessment_id.in_(subject_assessments)
                    )
                ),
                "rowcount",
                0,
            )
            or 0
        )
        subject_scenarios = select(ArenaScenarioORM.id).where(
            ArenaScenarioORM.owner_consultant_id == subject_id
        )
        counts["arena_sessions"] = (
            getattr(
                self._session.execute(
                    delete(ArenaSessionORM).where(
                        ArenaSessionORM.scenario_id.in_(subject_scenarios)
                    )
                ),
                "rowcount",
                0,
            )
            or 0
        )

        owned = {orm.__table__: orm for orm in _owned_orm_classes()}
        # metadata.sorted_tables is parent→child; reversed is child→parent, the safe delete order.
        for table in reversed(Base.metadata.sorted_tables):
            orm = owned.get(table)
            if orm is None or table.name == "scoring_runs":  # runs are anonymised, not deleted
                continue
            result = self._session.execute(delete(orm).where(orm.owner_consultant_id == subject_id))
            # Accumulate — module_rating_drafts / arena_sessions partly deleted cross-owner above.
            counts[table.name] = counts.get(table.name, 0) + (getattr(result, "rowcount", 0) or 0)

        consultant = self._require_consultant(subject_id)
        # Invitations are NOT owner-scoped but carry the subject's PII: the invite that created them
        # holds their email, and invites they sent carry their id. Scrub both (email captured BEFORE
        # the consultant row is anonymised below).
        inv_result = self._session.execute(
            delete(InvitationORM).where(
                (InvitationORM.email == consultant.email)
                | (InvitationORM.invited_by_consultant_id == subject_id)
            )
        )
        counts["invitations"] = getattr(inv_result, "rowcount", 0) or 0

        # Registry contacts carry the subject's PII but are not owner-scoped, so the loop above
        # never reaches them (GRS-0193 §7). Erase the subject's own rows, matched on the email
        # captured before the consultant row is anonymised below. Rows for OTHER people at the same
        # institution are untouched: they are different data subjects.
        registry_rows = self._registry_contacts_for_email(consultant.email)
        for registry_row in registry_rows:
            self._session.delete(registry_row)
        counts["registry_contacts"] = len(registry_rows)

        consultant.email = f"deleted-{subject_id}@anonymised.invalid"
        consultant.full_name = "[deleted]"
        consultant.hashed_password = "!"  # unusable — no login
        consultant.is_active = False
        self._session.add(consultant)

        self.record_audit(
            actor_consultant_id=principal.consultant_id,
            event_type=AuditEventType.GDPR_DELETION,
            resource_type="consultant",
            resource_id=subject_id,
            detail="Owned data erased; consultant anonymised; scoring runs de-identified.",
            now=now,
        )
        self._session.flush()
        return counts

    # ------------------------------------------------------------------ engagements (SCOPED)
    def create_engagement(
        self,
        principal: Principal,
        *,
        prospect_id: UUID,
        title: str,
        started_on: date | None = None,
        assessment_ids: tuple[UUID, ...] = (),
        deliverables: tuple[DeliverableSlot, ...] = (),
    ) -> Engagement:
        """Open an engagement against one of the principal's OWN contracted prospects, optionally
        linking finalised assessments. A cross-owner prospect/assessment is refused as not-found
        (no existence leak); an own-but-not-contracted prospect or an unfinalised assessment is an
        `EngagementLinkError`. The owner is the principal, never caller-supplied."""
        prospect = self.get_prospect(principal, prospect_id)  # raises NotFound/Scope on cross-owner
        if prospect.stage not in _ENGAGEABLE_STAGES:
            raise EngagementLinkError(
                f"Prospect {prospect_id} is at stage {prospect.stage.value}; an engagement links a "
                f"contracted (or beyond) prospect only."
            )
        for assessment_id in assessment_ids:
            assessment = self.get_assessment(
                principal, assessment_id
            )  # scoped: cross-owner refused
            if assessment.state != AssessmentState.FINALISED:
                raise EngagementLinkError(
                    f"Assessment {assessment_id} is not finalised; only finalised assessments link."
                )

        row = EngagementORM(
            owner_consultant_id=principal.consultant_id,
            prospect_id=prospect_id,
            title=title,
            status=EngagementStatus.CONTRACTED,
            started_on=started_on,
            assessment_ids_json=json.dumps([str(a) for a in assessment_ids]),
            deliverables_json=json.dumps([d.model_dump(mode="json") for d in deliverables]),
        )
        self._session.add(row)
        self._session.flush()
        return self._to_engagement(row)

    def get_engagement(self, principal: Principal, engagement_id: UUID) -> Engagement:
        return self._to_engagement(self._require_engagement(principal, engagement_id))

    def list_engagements(self, principal: Principal) -> list[Engagement]:
        stmt = select(EngagementORM)
        if not principal.is_admin:
            stmt = stmt.where(EngagementORM.owner_consultant_id == principal.consultant_id)
        rows = self._session.execute(stmt.order_by(EngagementORM.created_at)).scalars().all()
        result: list[Engagement] = []
        for row in rows:
            self._assert_can_access(principal, row.owner_consultant_id)  # belt and braces
            result.append(self._to_engagement(row))
        return result

    def append_comms_entry(
        self,
        principal: Principal,
        engagement_id: UUID,
        *,
        channel: CommsChannel,
        body: str,
        at: datetime | None = None,
    ) -> CommsLogEntry:
        """Append a communication-log entry to a scoped engagement. Append-only — the entry is
        inserted, never updated; the author is the principal."""
        self._require_engagement(principal, engagement_id)  # scope check
        row = CommsLogEntryORM(
            owner_consultant_id=principal.consultant_id,
            engagement_id=engagement_id,
            at=at or datetime.now(UTC),
            channel=channel.value,
            author_consultant_id=principal.consultant_id,
            body=body,
        )
        self._session.add(row)
        self._session.flush()
        return self._to_comms_entry(row)

    def link_assessment_to_engagement(
        self,
        principal: Principal,
        engagement_id: UUID,
        assessment_id: UUID,
        *,
        confirm_subject_mismatch: bool = False,
    ) -> Engagement:
        """Link a finalised assessment to one of the principal's OWN engagements (GRS-0039).

        Engagements can be opened before any assessment exists, so this closes the loop:
        contract -> open engagement -> run + finalise an assessment -> link it here -> generate
        deliverables. Same guards as engagement-open: a cross-owner (or missing)
        engagement/assessment is not-found (no existence leak); an unfinalised assessment or one
        already linked is an
        `EngagementLinkError` (409). The owner is the principal, never caller-supplied."""
        row = self._require_engagement(principal, engagement_id)  # scoped ORM row
        assessment = self.get_assessment(principal, assessment_id)  # scoped: cross-owner refused
        if assessment.state != AssessmentState.FINALISED:
            raise EngagementLinkError(
                f"Assessment {assessment_id} is not finalised; only finalised assessments link."
            )
        linked = json.loads(row.assessment_ids_json)
        if str(assessment_id) in linked:
            raise EngagementLinkError(
                f"Assessment {assessment_id} is already linked to this engagement."
            )

        # GRS-0241 scope 4. Until now this method checked ownership, finalisation and duplication —
        # and never that the assessment is ABOUT the engagement's client. The detail page offered a
        # dropdown of every finalised assessment the advisor owns, so one click linked Deutsche
        # Börse's scores to the WeBull engagement and nothing anywhere said otherwise. The
        # deliverable generated from that link would carry one firm's name over another firm's
        # numbers, which is the worst output this system can produce.
        #
        # Refused by default, overridable EXPLICITLY. The override exists because the match is on a
        # typed subject string and legitimate mismatches are real — a group entity assessed under
        # its parent's name, a rename mid-engagement. But it cannot happen by accident, and the
        # caller has to have been told what it is about to do.
        mismatch = self._subject_mismatch(row, assessment)
        if mismatch is not None and not confirm_subject_mismatch:
            engagement_client, assessment_subject = mismatch
            raise EngagementSubjectMismatchError(
                f"This engagement is for {engagement_client!r} but that assessment is about "
                f"{assessment_subject!r}. Linking it would put one firm's scores under another "
                f"firm's name on every deliverable. Confirm explicitly if the two really are the "
                f"same client."
            )

        linked.append(str(assessment_id))
        row.assessment_ids_json = json.dumps(linked)
        self._session.flush()
        return self._to_engagement(row)

    def _subject_mismatch(
        self, engagement: EngagementORM, assessment: Assessment
    ) -> tuple[str, str] | None:
        """(engagement client, assessment subject) when they disagree, else None.

        Compared case- and punctuation-insensitively, and an EMPTY subject is never a mismatch: a
        blank is an absence of evidence, and refusing on it would block a legitimate link with a
        message that names nothing. The comparison is deliberately loose in the safe direction —
        it exists to catch "Deutsche Börse vs WeBull", not to police "Ltd" against "Limited".
        """
        subject = (assessment.subject or "").strip()
        if not subject:
            return None
        prospect = self._session.get(ProspectORM, engagement.prospect_id)
        client = (prospect.company_name if prospect else "").strip()
        if not client:
            return None
        if _loose_name(client) == _loose_name(subject):
            return None
        # A containment match keeps "WeBull" and "WeBull Financial LLC" together, which is the
        # common honest case, without letting two unrelated firms through.
        a, b = _loose_name(client), _loose_name(subject)
        if a in b or b in a:
            return None
        return (client, subject)

    def _require_engagement(self, principal: Principal, engagement_id: UUID) -> EngagementORM:
        row = self._session.get(EngagementORM, engagement_id)
        if row is None:
            raise NotFoundError(f"Engagement {engagement_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        return row

    def _comms_for(self, engagement_id: UUID) -> list[CommsLogEntryORM]:
        stmt = (
            select(CommsLogEntryORM)
            .where(CommsLogEntryORM.engagement_id == engagement_id)
            .order_by(CommsLogEntryORM.at, CommsLogEntryORM.created_at)
        )
        return list(self._session.execute(stmt).scalars().all())

    # ------------------------------------------------------------------ deliverables (SCOPED)
    def create_deliverable(
        self,
        principal: Principal,
        *,
        engagement_id: UUID,
        deliverable_type: DeliverableType,
        title: str,
        mode: DeliverableMode,
        scoring_run_id: UUID | None,
        coefficient_version: str | None,
        content_hash: str | None,
        generated_at: datetime | None,
        ai_generated: bool = False,
    ) -> Deliverable:
        """Persist a deliverable's metadata against one of the principal's OWN engagements. The
        engagement is access-checked; the owner is the principal, never caller-supplied. The .docx
        is regenerated on download (no bytes stored)."""
        self.get_engagement(principal, engagement_id)  # scope check (cross-owner refused)
        row = DeliverableORM(
            owner_consultant_id=principal.consultant_id,
            engagement_id=engagement_id,
            type=deliverable_type.value,
            title=title,
            ai_generated=ai_generated,
            approval_status=ApprovalStatus.DRAFT.value,
            mode=mode.value,
            scoring_run_id=scoring_run_id,
            coefficient_version=coefficient_version,
            content_hash=content_hash,
            generated_at=generated_at,
        )
        self._session.add(row)
        self._session.flush()
        self.record_audit(
            actor_consultant_id=principal.consultant_id,
            event_type=AuditEventType.DELIVERABLE_GENERATED,
            resource_type="deliverable",
            resource_id=row.id,
            detail=deliverable_type.value,
            now=datetime.now(UTC),
        )
        return self._to_deliverable(row)

    def get_deliverable(self, principal: Principal, deliverable_id: UUID) -> Deliverable:
        return self._to_deliverable(self._require_deliverable(principal, deliverable_id))

    def list_deliverables_for_consultant(self, principal: Principal) -> list[DeliverableIndexRow]:
        """The advisor's OWN deliverables index (GRS-0186), newest-generated first. One query
        joining the deliverable to its engagement (title, prospect) and prospect (company name),
        filtered strictly to `principal`'s rows — self-only even for an admin (mirrors the
        `_own_prospects` rule, ADR-0016), never the whole org's. Null `generated_at` sorts last."""
        stmt = (
            select(DeliverableORM, EngagementORM, ProspectORM)
            .join(EngagementORM, DeliverableORM.engagement_id == EngagementORM.id)
            .join(ProspectORM, EngagementORM.prospect_id == ProspectORM.id)
            .where(DeliverableORM.owner_consultant_id == principal.consultant_id)
            .order_by(
                DeliverableORM.generated_at.is_(None),  # False (0) first → non-null before null
                DeliverableORM.generated_at.desc(),
                DeliverableORM.created_at.desc(),
            )
        )
        rows: list[DeliverableIndexRow] = []
        for deliverable, engagement, prospect in self._session.execute(stmt).all():
            rows.append(
                DeliverableIndexRow(
                    id=deliverable.id,
                    type=DeliverableType(deliverable.type),
                    title=deliverable.title,
                    mode=DeliverableMode(deliverable.mode),
                    generated_at=deliverable.generated_at,
                    engagement_id=engagement.id,
                    engagement_title=engagement.title,
                    prospect_id=prospect.id,
                    prospect_company_name=prospect.company_name,
                )
            )
        return rows

    def list_deliverables(self, principal: Principal, engagement_id: UUID) -> list[Deliverable]:
        self.get_engagement(principal, engagement_id)  # scope check on the parent
        stmt = (
            select(DeliverableORM)
            .where(DeliverableORM.engagement_id == engagement_id)
            .order_by(DeliverableORM.created_at)
        )
        rows = self._session.execute(stmt).scalars().all()
        result: list[Deliverable] = []
        for row in rows:
            self._assert_can_access(principal, row.owner_consultant_id)  # belt and braces
            result.append(self._to_deliverable(row))
        return result

    def _require_deliverable(self, principal: Principal, deliverable_id: UUID) -> DeliverableORM:
        row = self._session.get(DeliverableORM, deliverable_id)
        if row is None:
            raise NotFoundError(f"Deliverable {deliverable_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        return row

    @staticmethod
    def _to_deliverable(row: DeliverableORM) -> Deliverable:
        return Deliverable(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            engagement_id=row.engagement_id,
            type=DeliverableType(row.type),
            title=row.title,
            ai_generated=row.ai_generated,
            approval_status=ApprovalStatus(row.approval_status),
            approved_by_consultant_id=row.approved_by_consultant_id,
            mode=DeliverableMode(row.mode),
            scoring_run_id=row.scoring_run_id,
            coefficient_version=row.coefficient_version,
            content_hash=row.content_hash,
            generated_at=row.generated_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ------------------------------------------------------------------ AI narratives (SCOPED)
    def create_narrative(
        self,
        principal: Principal,
        *,
        deliverable_id: UUID,
        scoring_run_id: UUID,
        section: NarrativeSection,
        proposed_text: str,
        drafter_version: str,
        prompt_template_version: str,
        author_tier: ConsultantTier,
    ) -> AINarrative:
        """Persist an AI narrative PROPOSAL against one of the principal's OWN deliverables. The
        deliverable AND the scoring run are access-checked (the repository is the single scoping
        layer, #9); the owner is the principal. A proposal never carries an approval trail — that is
        a separate, human step (non-negotiable #8)."""
        self._require_deliverable(principal, deliverable_id)  # scope check (cross-owner refused)
        self.get_scoring_run_record(principal, scoring_run_id)  # scope the run too — never trusted
        row = AINarrativeORM(
            owner_consultant_id=principal.consultant_id,
            deliverable_id=deliverable_id,
            scoring_run_id=scoring_run_id,
            section=section.value,
            status=NarrativeStatus.PROPOSED.value,
            proposed_text=proposed_text,
            drafter_version=drafter_version,
            prompt_template_version=prompt_template_version,
            author_tier=author_tier,
        )
        self._session.add(row)
        self._session.flush()
        return self._to_ai_narrative(row)

    def approve_narrative(
        self,
        principal: Principal,
        *,
        narrative_id: UUID,
        final_text: str,
        edit_summary: str,
        approved_at: datetime,
    ) -> AINarrative:
        """Record human sign-off on one of the principal's OWN narratives: approver, timestamp, the
        final (possibly edited) text, and the edit diff. The seniority gate (PRD §5) is enforced by
        the caller before this point. Approving an already-approved narrative is refused."""
        row = self._require_ai_narrative(principal, narrative_id)
        if row.status == NarrativeStatus.APPROVED.value:
            raise RepositoryError(f"Narrative {narrative_id} is already approved.")
        row.status = NarrativeStatus.APPROVED.value
        row.final_text = final_text
        row.edit_summary = edit_summary
        row.approved_by_consultant_id = principal.consultant_id
        row.approved_at = approved_at
        self._session.flush()
        return self._to_ai_narrative(row)

    def get_narrative(self, principal: Principal, narrative_id: UUID) -> AINarrative:
        return self._to_ai_narrative(self._require_ai_narrative(principal, narrative_id))

    def list_narratives(self, principal: Principal, deliverable_id: UUID) -> list[AINarrative]:
        self._require_deliverable(principal, deliverable_id)  # scope check on the parent
        stmt = (
            select(AINarrativeORM)
            .where(AINarrativeORM.deliverable_id == deliverable_id)
            .order_by(AINarrativeORM.created_at)
        )
        rows = self._session.execute(stmt).scalars().all()
        result: list[AINarrative] = []
        for row in rows:
            self._assert_can_access(principal, row.owner_consultant_id)  # belt and braces
            result.append(self._to_ai_narrative(row))
        return result

    def _require_ai_narrative(self, principal: Principal, narrative_id: UUID) -> AINarrativeORM:
        row = self._session.get(AINarrativeORM, narrative_id)
        if row is None:
            raise NotFoundError(f"AI narrative {narrative_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        return row

    @staticmethod
    def _to_ai_narrative(row: AINarrativeORM) -> AINarrative:
        return AINarrative(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            deliverable_id=row.deliverable_id,
            scoring_run_id=row.scoring_run_id,
            section=NarrativeSection(row.section),
            status=NarrativeStatus(row.status),
            proposed_text=row.proposed_text,
            drafter_version=row.drafter_version,
            prompt_template_version=row.prompt_template_version,
            author_tier=ConsultantTier(row.author_tier),
            final_text=row.final_text,
            approved_by_consultant_id=row.approved_by_consultant_id,
            approved_at=row.approved_at,
            edit_summary=row.edit_summary,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ------------------------------------------------------------------ scoring runs (SCOPED)
    def create_scoring_run(
        self,
        principal: Principal,
        *,
        assessment_id: UUID,
        inputs: AssessmentInputs,
        result: AtlasResult,
        v_p10: float | None = None,
        v_p90: float | None = None,
        uncertainty_rating: str | None = None,
        uncertainty_version: str | None = None,
    ) -> ScoringRun:
        """Append an immutable scoring run owned by the principal. Versions are read from the result
        (the engine stamps them), the content hash is computed over inputs + versions, and the full
        inputs and result are stored. The owner is the principal — never caller-supplied."""
        digest = content_hash_for(
            inputs,
            result.engine_version,
            result.methodology_version,
            result.coefficient_version,
        )
        row = ScoringRunORM(
            owner_consultant_id=principal.consultant_id,
            assessment_id=assessment_id,
            engine_version=result.engine_version,
            methodology_version=result.methodology_version,
            coefficient_version=result.coefficient_version,
            uncertainty_version=uncertainty_version,
            content_hash=digest,
            inputs_json=inputs.model_dump_json(),
            result_json=result.model_dump_json(),
            v_index=result.composite.v_index,
            v_p10=v_p10,
            v_p90=v_p90,
            uncertainty_rating=uncertainty_rating,
            finalised=False,
        )
        self._session.add(row)
        self._session.flush()
        return self._to_scoring_run(row)

    def get_scoring_run(self, principal: Principal, run_id: UUID) -> ScoringRun:
        row = self._require_scoring_run(principal, run_id)
        return self._to_scoring_run(row)

    def list_scoring_runs(self, principal: Principal) -> list[ScoringRun]:
        stmt = select(ScoringRunORM)
        if not principal.is_admin:
            stmt = stmt.where(ScoringRunORM.owner_consultant_id == principal.consultant_id)
        rows = self._session.execute(stmt.order_by(ScoringRunORM.created_at)).scalars().all()
        result: list[ScoringRun] = []
        for row in rows:
            self._assert_can_access(principal, row.owner_consultant_id)  # belt and braces
            result.append(self._to_scoring_run(row))
        return result

    def finalise_scoring_run(self, principal: Principal, run_id: UUID) -> ScoringRun:
        """Lock a run's inputs (finalised False→True) — the ONE permitted state change on an
        otherwise append-only row. Re-finalising is a conflict; inputs/result/hash never change."""
        row = self._require_scoring_run(principal, run_id)
        if row.finalised:
            raise ConflictError(f"Scoring run {run_id} is already finalised; runs are immutable.")
        row.finalised = True
        self._session.add(row)
        self._session.flush()
        return self._to_scoring_run(row)

    def get_scoring_run_record(self, principal: Principal, run_id: UUID) -> StoredScoringRun:
        """The full immutable record (inputs + result JSON + hash) — for integrity verification and
        re-scoring. Scoped like every read."""
        row = self._require_scoring_run(principal, run_id)
        return StoredScoringRun(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            assessment_id=row.assessment_id,
            engine_version=row.engine_version,
            methodology_version=row.methodology_version,
            coefficient_version=row.coefficient_version,
            content_hash=row.content_hash,
            inputs_json=row.inputs_json,
            result_json=row.result_json,
            finalised=row.finalised,
        )

    def _require_scoring_run(self, principal: Principal, run_id: UUID) -> ScoringRunORM:
        row = self._session.get(ScoringRunORM, run_id)
        if row is None:
            raise NotFoundError(f"Scoring run {run_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        return row

    # ------------------------------------------------------------------ assessments (SCOPED)
    def create_assessment(
        self,
        principal: Principal,
        *,
        subject: str = "",
        provenance: RecordProvenance = RecordProvenance.PRODUCTION,
        entity_id: str | None = None,
    ) -> Assessment:
        """Create an empty draft assessment owned by the principal (owner never caller-supplied).
        `provenance` is set here and is IMMUTABLE thereafter (ADR-0029) — a sandbox/demo record is
        never promotable to production. `entity_id` is the canonical company the subject resolved to
        (GRS-0100), or null for a manual/unlinked subject; the caller validates it against the
        registry before passing it (the repository stores what it's given)."""
        row = AssessmentORM(
            owner_consultant_id=principal.consultant_id,
            subject=subject,
            entity_id=entity_id,
            state=AssessmentState.DRAFT.value,
            provenance=provenance.value,
            document_json=AssessmentDocument(subject=subject).model_dump_json(),
        )
        self._session.add(row)
        self._session.flush()
        return self._to_assessment(row)

    def list_assessments_for_entity(self, principal: Principal, entity_id: str) -> list[Assessment]:
        """The caller's OWN assessments of one canonical company (GRS-0100 dedup). Owner-scoped —
        the count is a consultant's own book, never a cross-owner leak (#9)."""
        rows = (
            self._session.execute(
                select(AssessmentORM)
                .where(
                    AssessmentORM.owner_consultant_id == principal.consultant_id,
                    AssessmentORM.entity_id == entity_id,
                )
                .order_by(AssessmentORM.created_at)
            )
            .scalars()
            .all()
        )
        return [self._to_assessment(r) for r in rows]

    def get_assessment(self, principal: Principal, assessment_id: UUID) -> Assessment:
        return self._to_assessment(self._require_assessment(principal, assessment_id))

    def delete_assessment(
        self,
        principal: Principal,
        assessment_id: UUID,
        *,
        discard_scoring_runs: bool = False,
        delete_production_record: bool = False,
    ) -> None:
        """Remove ONE assessment the caller owns, named by id (GRS-0177 staging cleanup).

        Three guards, each defaulting to refusal.

        A **production** record is refused unless the caller passes
        `delete_production_record=True` AND is the founder or an admin. That combination is not a
        convenience: it is a founder saying, about one named record, that it is a mis-click rather
        than work. No criteria-based caller can reach it, because the flag is per call and the
        method takes one id. Every such deletion writes an audit event naming the record. See the
        2026-07-29 amendment to ADR-0047.

        A record carrying a **scoring run** is refused by default, because runs are immutable and
        append-only (#6) — deleting the assessment would either orphan the run or destroy it.
        `discard_scoring_runs=True` is the caller stating, in the call itself, that this record's
        runs should go with it. See ADR-0047 for why that carve-out does not weaken #6.

        There is no bulk or wildcard form. Every deletion names one id.
        """
        row = self._require_assessment(principal, assessment_id)
        is_production = row.provenance == RecordProvenance.PRODUCTION.value
        if is_production and not delete_production_record:
            raise ConflictError(
                f"Assessment {assessment_id} is a production record and cannot be deleted here. "
                f"Deleting one is a founder decision, taken per record: call with "
                f"delete_production_record=True."
            )
        if is_production and not (principal.is_founder or principal.is_admin):
            raise ScopeViolationError(
                "Only the founder or an admin may delete a production record."
            )
        # Any stored run at all is the bar, not just a flagged one: runs are append-only, so a row
        # existing is exactly the thing that must not be destroyed. A finalised assessment always
        # has one, which is why the state check and the run check agree in practice.
        runs = (
            self._session.execute(
                select(ScoringRunORM).where(ScoringRunORM.assessment_id == assessment_id)
            )
            .scalars()
            .all()
        )
        if (row.state == AssessmentState.FINALISED.value or runs) and not discard_scoring_runs:
            raise ConflictError(
                f"Assessment {assessment_id} is finalised or carries {len(runs)} immutable "
                f"scoring run(s). Retire the record instead of deleting it, or — for a demo or "
                f"sandbox record whose runs are seeded illustration — call with "
                f"discard_scoring_runs=True."
            )

        # Children first, so no FK is left dangling.
        self._session.execute(
            delete(ModuleRatingDraftORM).where(ModuleRatingDraftORM.assessment_id == assessment_id)
        )
        self._session.execute(
            delete(CommitteeDecisionORM).where(CommitteeDecisionORM.assessment_id == assessment_id)
        )
        # Three tables point at a scoring run by id rather than at the assessment, so removing the
        # runs without them would leave rows referring to a run that no longer exists. Orphaned
        # rows are exactly the silent-inconsistency failure mode #3 exists to prevent, so they go
        # in the same transaction.
        run_ids = [run.id for run in runs]
        if run_ids:
            self._session.execute(
                delete(AINarrativeORM).where(AINarrativeORM.scoring_run_id.in_(run_ids))
            )
            self._session.execute(
                delete(PredictionORM).where(PredictionORM.scoring_run_id.in_(run_ids))
            )
            self._session.execute(
                delete(DeliverableORM).where(DeliverableORM.scoring_run_id.in_(run_ids))
            )
        self._session.execute(
            delete(ScoringRunORM).where(ScoringRunORM.assessment_id == assessment_id)
        )
        subject = row.subject
        self._session.delete(row)
        self._session.flush()
        if is_production:
            # Removing a production record is the one deletion here that could ever have destroyed
            # real work, so it leaves a permanent trace of who did it and to what. The audit log is
            # append-only, so this survives the record it describes.
            self.record_audit(
                actor_consultant_id=principal.consultant_id,
                event_type=AuditEventType.ASSESSMENT_DELETED,
                now=datetime.now(UTC),
                resource_type="assessment",
                resource_id=assessment_id,
                detail=(
                    f"Deleted production record {subject!r} "
                    f"({len(run_ids)} scoring run(s)) by founder decision."
                ),
            )

    def list_assessments(self, principal: Principal) -> list[Assessment]:
        stmt = select(AssessmentORM)
        if not principal.is_admin:
            stmt = stmt.where(AssessmentORM.owner_consultant_id == principal.consultant_id)
        rows = self._session.execute(stmt.order_by(AssessmentORM.created_at)).scalars().all()
        out: list[Assessment] = []
        for row in rows:
            self._assert_can_access(principal, row.owner_consultant_id)  # belt and braces
            out.append(self._to_assessment(row))
        return out

    def list_brokerage_portfolio(self, principal: Principal) -> list[BrokeragePortfolioEntry]:
        """The advisor's "Your Brokerages" portfolio (GRS-0071): one summary row per assessment,
        newest-touched first, each carrying its segment (from the business profile) and — when
        finalised — its last Platform Value + uncertainty rating from the immutable scoring run.
        Reuses `list_assessments` for scoping, so the owner-only guarantee is inherited, not
        re-implemented."""
        from bcap_contracts.registry import load_profiles

        from grassmarket.assessments.service import c_index_of
        from grassmarket.atlas.active import profile_key_of, profile_scoring_context

        profiles = load_profiles()  # key -> ProfileDef, for the operating-model display name
        # assessment_id -> prospect_id for the caller's engagements (GRS-0186), built once so the
        # portfolio row can link to the client record. A link is recorded only where it genuinely
        # exists; an unlinked assessment stays None (never a fabricated link).
        import json as _json

        linked_prospect: dict[UUID, UUID] = {}
        eng_rows = (
            self._session.execute(
                select(EngagementORM).where(
                    EngagementORM.owner_consultant_id == principal.consultant_id
                )
            )
            .scalars()
            .all()
        )
        for eng in eng_rows:
            for aid in _json.loads(eng.assessment_ids_json or "[]"):
                linked_prospect.setdefault(UUID(str(aid)), eng.prospect_id)
        entries: list[BrokeragePortfolioEntry] = []
        for a in self.list_assessments(principal):
            v_index = None
            v_p10 = None
            v_p90 = None
            uncertainty_rating = None
            if a.scoring_run_id is not None:
                run = self.get_scoring_run(principal, a.scoring_run_id)  # own + exists
                v_index = run.v_index
                # The run's stored band travels with the point (GRS-0166) so the finalised
                # wizard rail can quote the SAME locked score+band as this row + deliverable.
                v_p10 = run.v_p10
                v_p90 = run.v_p90
                uncertainty_rating = run.uncertainty_rating
            # C is reported alongside V (ADR-0023): deterministic and document-derived, so it is
            # recomputed here from the locked/current document under the profile's registry view —
            # no immutable run needed, None when C is not yet scoreable.
            profile_key = profile_key_of(a.document)
            c_registry, _ = profile_scoring_context(profile_key)
            c_index = c_index_of(a.document, c_registry)
            # Segment reads the free-text profile segment first; when it is blank, fall back to the
            # operating-model NAME (retail is the scoring default) so the column is never a bare "—"
            # for an assessment that plainly has an operating model (GRS-0163).
            free_text = a.document.profile.segment if a.document.profile else None
            profile_def = profiles.get(profile_key)
            segment = free_text or (profile_def.name if profile_def else None)
            entries.append(
                BrokeragePortfolioEntry(
                    assessment_id=a.id,
                    subject=a.subject or "Untitled assessment",
                    segment=segment,
                    state=a.state,
                    provenance=a.provenance,
                    v_index=v_index,
                    v_p10=v_p10,
                    v_p90=v_p90,
                    c_index=c_index,
                    uncertainty_rating=uncertainty_rating,
                    # Coverage against the assessment's OWN profile view (GRS-0168) — the same
                    # denominator the wizard's "of applicable" figure uses.
                    coverage=_document_coverage(a.document, c_registry),
                    finalised_at=a.finalised_at,
                    updated_at=a.updated_at,
                    linked_prospect_id=linked_prospect.get(a.id),
                )
            )
        entries.sort(key=lambda e: e.updated_at, reverse=True)
        return entries

    def list_assessments_for_committee(self, principal: Principal) -> list[Assessment]:
        """Every in-progress assessment across owners — so a committee member/admin can find the
        work that needs their sign-off. NOT owner-scoped (committee visibility, ADR-0011); a plain
        consultant is refused. Finalised assessments are excluded (their gate has cleared)."""
        if not (principal.is_committee or principal.is_admin):
            raise ScopeViolationError(
                "Only a committee member or an admin may list assessments for committee review."
            )
        stmt = (
            select(AssessmentORM)
            .where(AssessmentORM.state == AssessmentState.IN_PROGRESS.value)
            .order_by(AssessmentORM.updated_at.desc())
        )
        rows = self._session.execute(stmt).scalars().all()
        return [self._to_assessment(r) for r in rows]

    def update_assessment(
        self, principal: Principal, assessment_id: UUID, *, document: AssessmentDocument
    ) -> Assessment:
        """Autosave: replace the intermediate document. A partial document is valid and saved
        without scoring. A FINALISED assessment refuses edits (its inputs are locked).

        The dual-rating governance fields (`rater_ids`/`consensus`/`dissent_note`) are STRIPPED from
        an autosaved document: they are set only by `resolve_module_consensus`, which is computed
        from real submitted drafts. Were an autosave allowed to carry them, a lead could PUT a
        document with fabricated `consensus=True, rater_ids=[…]` and finalise with no second rater —
        the finalise gate reads these fields, so §9 would be advisory (ADR-0010). Editing a
        subcomponent legitimately invalidates any prior consensus on it, so clearing is right too.
        """
        row = self._require_assessment(principal, assessment_id)
        if row.state == AssessmentState.FINALISED.value:
            raise ConflictError(
                f"Assessment {assessment_id} is finalised; its inputs are locked (#6)."
            )
        row.document_json = _strip_governance_fields(document).model_dump_json()
        row.subject = document.subject
        row.state = AssessmentState.IN_PROGRESS.value
        self._session.add(row)
        self._session.flush()
        return self._to_assessment(row)

    def finalise_assessment(
        self,
        principal: Principal,
        assessment_id: UUID,
        *,
        scoring_run_id: UUID,
        engine_version: str,
        methodology_version: str,
        coefficient_version: str,
        uncertainty_version: str,
        finalised_at: datetime,
    ) -> Assessment:
        """Lock the assessment's inputs: state → FINALISED, stamped and linked to its immutable
        scoring run. Re-finalising is refused. (The run is created by the caller in the same
        transaction — see the live-score / finalise service.)"""
        row = self._require_assessment(principal, assessment_id)
        if row.state == AssessmentState.FINALISED.value:
            raise ConflictError(f"Assessment {assessment_id} is already finalised.")
        row.state = AssessmentState.FINALISED.value
        row.finalised_at = finalised_at
        row.scoring_run_id = scoring_run_id
        row.engine_version = engine_version
        row.methodology_version = methodology_version
        row.coefficient_version = coefficient_version
        row.uncertainty_version = uncertainty_version
        self._session.add(row)
        self.record_audit(
            actor_consultant_id=principal.consultant_id,
            event_type=AuditEventType.ASSESSMENT_FINALISED,
            resource_type="assessment",
            resource_id=assessment_id,
            now=finalised_at,
        )
        # GRS-0131 derived certification evidence from peer participation: a shadow credit for each
        # co-rater, an observed-lead credit for the lead. With dual rating retired (ADR-0041) there
        # are no co-raters, so the shadow half now derives nothing and the observed-lead half would
        # award "observed" credit with nobody observing. Awarding evidence for something that did
        # not happen is worse than awarding none, so the call is removed here.
        #
        # `_auto_credit_participation` stays below, dormant with its unit test, so re-mounting peer
        # rating restores this in one line. Evidence is recorded meanwhile through
        # `log_shadow_assessment`, `log_observed_lead`, and the audited OVERRIDE path — all of which
        # need a human to assert that the thing happened.
        self._session.flush()
        return self._to_assessment(row)

    def _has_derived_cert_event(
        self, advisor_id: UUID, assessment_id: UUID, kind: CertificationEventKind
    ) -> bool:
        """Whether this exact derived credit already exists — so re-finalising never double-adds."""
        return (
            self._session.execute(
                select(CertificationEventORM.id).where(
                    CertificationEventORM.owner_consultant_id == advisor_id,
                    CertificationEventORM.assessment_id == assessment_id,
                    CertificationEventORM.kind == kind.value,
                )
            ).first()
            is not None
        )

    def _auto_credit_participation(self, assessment: AssessmentORM, occurred_at: datetime) -> None:
        """Derive certification evidence from real participation in a finalised assessment
        (GRS-0131): every non-lead rater earns a *shadow* credit, the lead earns an *observed-lead*
        credit — each once per assessment (idempotent via `assessment_id`). Only PRODUCTION count; a
        sandbox/demo run is training, never real evidence (ADR-0029)."""
        if RecordProvenance(assessment.provenance) is not RecordProvenance.PRODUCTION:
            return
        aid = assessment.id
        lead_id = assessment.owner_consultant_id

        rater_ids = {
            r
            for (r,) in self._session.execute(
                select(ModuleRatingDraftORM.owner_consultant_id)
                .where(ModuleRatingDraftORM.assessment_id == aid)
                .distinct()
            ).all()
        }
        # Shadow credit for every co-rater who was not the lead (leading is observed-lead, below).
        for rater_id in sorted(rater_ids - {lead_id}, key=str):
            if self._has_derived_cert_event(rater_id, aid, CertificationEventKind.SHADOW_LOGGED):
                continue
            record = self._get_or_create_cert_record(rater_id)
            record.shadow_count += 1
            self._append_cert_event(
                rater_id,
                CertificationEventKind.SHADOW_LOGGED,
                lead_id,
                occurred_at,
                detail=f"auto: co-rated finalised assessment (count={record.shadow_count})",
                assessment_id=aid,
            )

        # Observed-lead credit for the lead — they led a finalised assessment, once.
        if not self._has_derived_cert_event(
            lead_id, aid, CertificationEventKind.OBSERVED_LEAD_LOGGED
        ):
            record = self._get_or_create_cert_record(lead_id)
            record.observed_lead_logged = True
            self._append_cert_event(
                lead_id,
                CertificationEventKind.OBSERVED_LEAD_LOGGED,
                lead_id,
                occurred_at,
                detail="auto: led a finalised assessment",
                assessment_id=aid,
            )

    def _require_assessment(self, principal: Principal, assessment_id: UUID) -> AssessmentORM:
        row = self._session.get(AssessmentORM, assessment_id)
        if row is None:
            raise NotFoundError(f"Assessment {assessment_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        return row

    @staticmethod
    def _to_assessment(row: AssessmentORM) -> Assessment:
        return Assessment(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            subject=row.subject,
            entity_id=row.entity_id,
            state=AssessmentState(row.state),
            document=AssessmentDocument.model_validate_json(row.document_json),
            provenance=RecordProvenance(row.provenance),
            review_requested_at=row.review_requested_at,
            finalised_at=row.finalised_at,
            scoring_run_id=row.scoring_run_id,
            engine_version=row.engine_version,
            methodology_version=row.methodology_version,
            coefficient_version=row.coefficient_version,
            uncertainty_version=row.uncertainty_version,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # --------------------------------------------------- founder review gate (GRS-0188, ADR-0041)
    # The network is one founder and a handful of advisors. Peer rating and committee sign-off were
    # built for a scale it has not reached; the founder signs what goes out instead. The whole
    # mechanism is a hash comparison: an approval names the document version it cleared, and it
    # clears the gate only while that is still the current version. Editing re-opens review by
    # arithmetic rather than by a state machine, so there is no way to be approved-but-changed.

    @staticmethod
    def _document_hash(row: AssessmentORM) -> str:
        """sha256 of the stored document. Computed here from what is in the database, never taken
        from a caller: an approval that could name its own hash would approve nothing."""
        return hashlib.sha256(row.document_json.encode("utf-8")).hexdigest()

    def request_founder_review(self, principal: Principal, assessment_id: UUID) -> Assessment:
        """The advisor asks the founder to review this document. Idempotent: asking again just
        moves the timestamp, which is what "I've made changes, please look again" means."""
        row = self._require_assessment(principal, assessment_id)
        if row.state == AssessmentState.FINALISED.value:
            raise ConflictError(
                f"Assessment {assessment_id} is already finalised; there is nothing left to review."
            )
        row.review_requested_at = datetime.now(UTC)
        self._session.flush()
        return self._to_assessment(row)

    def record_founder_approval(self, principal: Principal, assessment_id: UUID) -> FounderApproval:
        """The founder signs off the document as it stands right now.

        Only the founder may call this. Not an admin, and not the advisor who owns the record:
        the point of the gate is that one named person signs what leaves the building, so an
        admin bypass would quietly reintroduce self-approval (#8)."""
        if not principal.is_founder:
            raise ScopeViolationError(
                "Only the founder reviewer may approve a document for release (ADR-0041)."
            )
        row = self._session.get(AssessmentORM, assessment_id)
        if row is None:
            raise NotFoundError(f"Assessment {assessment_id} not found.")
        if row.state == AssessmentState.FINALISED.value:
            raise ConflictError(
                f"Assessment {assessment_id} is already finalised; approval would change nothing."
            )
        now = datetime.now(UTC)
        approval = FounderApprovalORM(
            owner_consultant_id=row.owner_consultant_id,
            assessment_id=assessment_id,
            document_hash=self._document_hash(row),
            approved_by_consultant_id=principal.consultant_id,
            approved_at=now,
        )
        self._session.add(approval)
        self._session.flush()
        self.record_audit(
            actor_consultant_id=principal.consultant_id,
            event_type=AuditEventType.FOUNDER_APPROVAL,
            now=now,
            resource_type="assessment",
            resource_id=assessment_id,
            detail=f"Approved document {approval.document_hash[:12]} for release.",
        )
        return self._to_founder_approval(approval)

    def current_founder_approval(self, assessment_id: UUID) -> FounderApproval | None:
        """The newest approval that still matches the document, or None.

        Unscoped by design: this is the gate itself, called from the finalise and deliverable
        paths where the caller's access has already been established. It reveals nothing a caller
        could not already see about a record they hold."""
        row = self._session.get(AssessmentORM, assessment_id)
        if row is None:
            raise NotFoundError(f"Assessment {assessment_id} not found.")
        current = self._document_hash(row)
        stmt = (
            select(FounderApprovalORM)
            .where(
                FounderApprovalORM.assessment_id == assessment_id,
                FounderApprovalORM.document_hash == current,
            )
            .order_by(FounderApprovalORM.approved_at.desc())
        )
        approval = self._session.execute(stmt).scalars().first()
        return self._to_founder_approval(approval) if approval is not None else None

    # --- Report-scoped founder approval (GRS-0245) ------------------------------------------
    #
    # The same rule as the assessment gate, bound to a different artefact. GRS-0245 measured the
    # gap: `current_founder_approval` matches against the ASSESSMENT document, the report prose
    # lives in another table and is written after finalisation, so a founder approval of the
    # assessment says nothing about the words that actually reach the client.

    @staticmethod
    def _prose_hash(sections_json: str) -> str:
        """sha256 of the stored prose. Computed from the database, never taken from a caller."""
        return hashlib.sha256(sections_json.encode("utf-8")).hexdigest()

    def _report_prose_row(self, deliverable_id: UUID) -> ClientReportProseORM | None:
        stmt = select(ClientReportProseORM).where(
            ClientReportProseORM.deliverable_id == deliverable_id
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def request_report_review(self, principal: Principal, deliverable_id: UUID) -> None:
        """The advisor asks the founder to sign off this report. Idempotent, like its assessment
        twin: asking again moves the timestamp, which is what "I have made changes" means."""
        self._require_deliverable(principal, deliverable_id)
        row = self._report_prose_row(deliverable_id)
        if row is None:
            raise ConflictError(
                "This report has no prose yet, so there is nothing for the founder to read."
            )
        row.review_requested_at = datetime.now(UTC)
        self._session.flush()

    def current_report_approval(self, deliverable_id: UUID) -> FounderApproval | None:
        """The approval that currently clears this report's prose, or None.

        None both when nothing was ever approved and when the prose changed since — the same
        deliberate conflation the assessment gate makes. What matters is whether the words about to
        reach a client are the words the founder read.

        Unscoped, like `current_founder_approval`: this is the gate itself, called from paths where
        the caller's access is already established.
        """
        row = self._report_prose_row(deliverable_id)
        if row is None:
            return None
        current = self._prose_hash(row.sections_json)
        stmt = (
            select(FounderApprovalORM)
            .where(
                FounderApprovalORM.deliverable_id == deliverable_id,
                FounderApprovalORM.document_hash == current,
            )
            .order_by(FounderApprovalORM.approved_at.desc())
        )
        approval = self._session.execute(stmt).scalars().first()
        return self._to_founder_approval(approval) if approval is not None else None

    def record_report_approval(self, principal: Principal, deliverable_id: UUID) -> FounderApproval:
        """The founder signs off the report's prose as it stands. Founder only — an admin bypass
        would quietly reintroduce self-approval, which is the thing ADR-0041 exists to prevent."""
        if not principal.is_founder:
            raise ScopeViolationError(
                "Only the founder reviewer may approve a client report for release (ADR-0041)."
            )
        deliverable = self._session.get(DeliverableORM, deliverable_id)
        if deliverable is None:
            raise NotFoundError(f"Deliverable {deliverable_id} not found.")
        row = self._report_prose_row(deliverable_id)
        if row is None:
            raise ConflictError("This report has no prose yet, so there is nothing to approve.")
        now = datetime.now(UTC)
        approval = FounderApprovalORM(
            owner_consultant_id=deliverable.owner_consultant_id,
            assessment_id=self._assessment_id_for_deliverable(deliverable),
            deliverable_id=deliverable_id,
            document_hash=self._prose_hash(row.sections_json),
            # The words the founder actually read, kept so the queue can show what changed rather
            # than only that something did.
            content_json=row.sections_json,
            approved_by_consultant_id=principal.consultant_id,
            approved_at=now,
        )
        self._session.add(approval)
        self._session.flush()
        return self._to_founder_approval(approval)

    def _assessment_id_for_deliverable(self, deliverable: DeliverableORM) -> UUID:
        """The assessment behind a deliverable, via its scoring run. Kept on the approval row so
        report approvals join and scope exactly like assessment ones."""
        record = self._session.get(ScoringRunORM, deliverable.scoring_run_id)
        if record is None:
            raise NotFoundError(
                f"Deliverable {deliverable.id} has no scoring run to attribute an approval to."
            )
        return record.assessment_id

    def report_was_ever_approved(self, deliverable_id: UUID) -> bool:
        """Whether the founder has signed this report off at ANY version.

        Distinct from `current_report_approval`, which asks whether the CURRENT words are cleared.
        The difference is what lets the refusal say "approved and then edited" rather than "not
        approved", which are different problems with different next actions.
        """
        stmt = select(FounderApprovalORM.id).where(
            FounderApprovalORM.deliverable_id == deliverable_id
        )
        return self._session.execute(stmt).first() is not None

    def report_sections_changed_since_approval(
        self, principal: Principal, deliverable_id: UUID
    ) -> tuple[str, ...]:
        """Which of the six sections differ from the last approved version (GRS-0245 scope 4).

        Empty when nothing was ever approved — there is no diff against nothing, and calling the
        whole report "changed" would tell the founder to re-read work they have never read once.
        The caller distinguishes the two cases by whether a prior approval exists at all.
        """
        self._require_deliverable(principal, deliverable_id)
        row = self._report_prose_row(deliverable_id)
        if row is None:
            return ()
        stmt = (
            select(FounderApprovalORM)
            .where(
                FounderApprovalORM.deliverable_id == deliverable_id,
                FounderApprovalORM.content_json.is_not(None),
            )
            .order_by(FounderApprovalORM.approved_at.desc())
        )
        previous = self._session.execute(stmt).scalars().first()
        if previous is None or previous.content_json is None:
            return ()
        try:
            before = json.loads(previous.content_json)
            after = json.loads(row.sections_json)
        except json.JSONDecodeError:  # pragma: no cover - stored by us, always valid
            return ()
        keys = sorted(set(before) | set(after))
        return tuple(k for k in keys if before.get(k) != after.get(k))

    def list_founder_review_queue(self, principal: Principal) -> list[FounderReviewQueueEntry]:
        """Everything waiting on the founder, oldest request first.

        Production records only. A demo or sandbox record self-approves under ADR-0029 and has no
        client on the other end, so putting one in this queue would waste the founder's attention
        on work that is not going anywhere."""
        if not (principal.is_founder or principal.is_admin):
            raise ScopeViolationError("Only the founder reviewer may read the review queue.")
        stmt = (
            select(AssessmentORM)
            .where(
                AssessmentORM.review_requested_at.is_not(None),
                AssessmentORM.state != AssessmentState.FINALISED.value,
                AssessmentORM.provenance == RecordProvenance.PRODUCTION.value,
            )
            .order_by(AssessmentORM.review_requested_at)
        )
        entries: list[FounderReviewQueueEntry] = []
        for row in self._session.execute(stmt).scalars().all():
            current = self._document_hash(row)
            approvals = (
                self._session.execute(
                    select(FounderApprovalORM).where(FounderApprovalORM.assessment_id == row.id)
                )
                .scalars()
                .all()
            )
            if any(a.document_hash == current for a in approvals):
                continue  # already signed at this version — not waiting on anyone
            requested_at = row.review_requested_at
            if requested_at is None:  # pragma: no cover - the query filters these out
                # The query says is_not(None), so reaching here means the filter and this loop
                # have drifted apart. Refuse rather than invent a request time (#3).
                raise ConflictError(
                    f"Assessment {row.id} is in the review queue with no request time."
                )
            advisor = self._require_consultant(row.owner_consultant_id)
            entries.append(
                FounderReviewQueueEntry(
                    id=row.id,
                    owner_consultant_id=row.owner_consultant_id,
                    assessment_id=row.id,
                    subject=row.subject,
                    advisor_name=advisor.full_name,
                    advisor_email=advisor.email,
                    requested_at=requested_at,
                    document_hash=current,
                    # An approval at some OTHER hash means this was signed and then edited. Saying
                    # so is the difference between "read this" and "read what changed".
                    previously_approved=bool(approvals),
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
            )
        entries.extend(self._report_review_queue())
        entries.sort(key=lambda e: e.requested_at)
        return entries

    def _report_review_queue(self) -> list[FounderReviewQueueEntry]:
        """Client reports awaiting sign-off (GRS-0245 scope 4), in the same queue as assessments.

        Production records only, for the same reason the assessment queue filters them: a demo or
        sandbox report is watermarked on every rendition (GRS-0229) and has no client on the other
        end, so it is not waiting on anyone.
        """
        stmt = select(ClientReportProseORM).where(
            ClientReportProseORM.review_requested_at.is_not(None)
        )
        out: list[FounderReviewQueueEntry] = []
        for prose in self._session.execute(stmt).scalars().all():
            deliverable = self._session.get(DeliverableORM, prose.deliverable_id)
            if deliverable is None:  # pragma: no cover - FK guarantees it
                continue
            record = self._session.get(ScoringRunORM, deliverable.scoring_run_id)
            if record is None:  # pragma: no cover - a deliverable always has its run
                continue
            assessment = self._session.get(AssessmentORM, record.assessment_id)
            if assessment is None or assessment.provenance != RecordProvenance.PRODUCTION.value:
                continue
            current = self._prose_hash(prose.sections_json)
            approvals = (
                self._session.execute(
                    select(FounderApprovalORM).where(
                        FounderApprovalORM.deliverable_id == prose.deliverable_id
                    )
                )
                .scalars()
                .all()
            )
            if any(a.document_hash == current for a in approvals):
                continue  # signed at this version — not waiting on anyone
            requested_at = prose.review_requested_at
            if requested_at is None:  # pragma: no cover - the query filters these out
                raise ConflictError(
                    f"Report {prose.deliverable_id} is in the review queue with no request time."
                )
            advisor = self._require_consultant(prose.owner_consultant_id)
            changed = self._changed_sections_from_rows(prose, approvals)
            out.append(
                FounderReviewQueueEntry(
                    id=prose.deliverable_id,
                    owner_consultant_id=prose.owner_consultant_id,
                    assessment_id=record.assessment_id,
                    deliverable_id=prose.deliverable_id,
                    subject=assessment.subject,
                    advisor_name=advisor.full_name,
                    advisor_email=advisor.email,
                    requested_at=requested_at,
                    document_hash=current,
                    previously_approved=bool(approvals),
                    changed_sections=changed,
                    created_at=prose.created_at,
                    updated_at=prose.updated_at,
                )
            )
        return out

    @staticmethod
    def _changed_sections_from_rows(
        prose: ClientReportProseORM, approvals: Sequence[FounderApprovalORM]
    ) -> tuple[str, ...]:
        """Which sections differ from the most recent approval that stored its content.

        Empty on a first review — there is nothing to diff against, and calling every section
        "changed" would tell the founder to re-read work they have never read once.
        """
        with_content = [a for a in approvals if a.content_json is not None]
        if not with_content:
            return ()
        previous = max(with_content, key=lambda a: a.approved_at)
        try:
            before = json.loads(previous.content_json or "{}")
            after = json.loads(prose.sections_json)
        except json.JSONDecodeError:  # pragma: no cover - stored by us, always valid
            return ()
        keys = sorted(set(before) | set(after))
        return tuple(k for k in keys if before.get(k) != after.get(k))

    @staticmethod
    def _to_founder_approval(row: FounderApprovalORM) -> FounderApproval:
        return FounderApproval(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            assessment_id=row.assessment_id,
            document_hash=row.document_hash,
            approved_by_consultant_id=row.approved_by_consultant_id,
            approved_at=row.approved_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ------------------------------------------------------- dual rating (SCOPED, Methodology §9)
    # "Solo ratings are drafts, never deliverables." A module is rated by ≥2 consultants who work
    # BLIND of each other until both submit; the lead then resolves consensus per subcomponent, with
    # a mandatory dissent note where they differed. Scoping widens here — an assigned rater who is
    # not the assessment owner may reach the rating surface (ADR-0010) — but never the owner's
    # document editing or finalisation, which stay lead-only.

    def _is_rater_on(self, assessment_id: UUID, consultant_id: UUID) -> bool:
        stmt = select(ModuleRatingDraftORM.id).where(
            ModuleRatingDraftORM.assessment_id == assessment_id,
            ModuleRatingDraftORM.owner_consultant_id == consultant_id,
        )
        return self._session.execute(stmt).first() is not None

    def _require_rating_access(self, principal: Principal, assessment_id: UUID) -> AssessmentORM:
        """The lead (owner), an assigned rater, or an admin may reach the rating workflow. Anyone
        else is refused loudly (a 404 at the boundary — the API never reveals the assessment)."""
        row = self._session.get(AssessmentORM, assessment_id)
        if row is None:
            raise NotFoundError(f"Assessment {assessment_id} not found.")
        if (
            principal.is_admin
            or row.owner_consultant_id == principal.consultant_id
            or self._is_rater_on(assessment_id, principal.consultant_id)
        ):
            return row
        raise ScopeViolationError(
            "Principal is neither the lead, an assigned rater, nor an admin for this assessment "
            "(data scoping is absolute, CLAUDE.md #9; rating access widened per ADR-0010)."
        )

    def _refuse_if_finalised(self, assessment_id: UUID) -> None:
        """A finalised assessment's inputs are locked (#6) — no draft mutation touches them."""
        row = self._session.get(AssessmentORM, assessment_id)
        if row is not None and row.state == AssessmentState.FINALISED.value:
            raise ConflictError(
                f"Assessment {assessment_id} is finalised; its inputs are locked (#6)."
            )

    def _module_drafts(self, assessment_id: UUID, module_key: str) -> list[ModuleRatingDraftORM]:
        stmt = (
            select(ModuleRatingDraftORM)
            .where(
                ModuleRatingDraftORM.assessment_id == assessment_id,
                ModuleRatingDraftORM.module_key == module_key,
            )
            .order_by(ModuleRatingDraftORM.created_at)
        )
        return list(self._session.execute(stmt).scalars().all())

    def _require_own_draft(
        self, principal: Principal, assessment_id: UUID, module_key: str
    ) -> ModuleRatingDraftORM:
        stmt = select(ModuleRatingDraftORM).where(
            ModuleRatingDraftORM.assessment_id == assessment_id,
            ModuleRatingDraftORM.module_key == module_key,
            ModuleRatingDraftORM.owner_consultant_id == principal.consultant_id,
        )
        row = self._session.execute(stmt).scalar_one_or_none()
        if row is None:
            raise NotFoundError(
                f"You are not assigned to rate module {module_key} on this assessment."
            )
        return row

    def assign_rater(
        self,
        principal: Principal,
        assessment_id: UUID,
        *,
        module_key: str,
        rater_consultant_id: UUID,
    ) -> ModuleRatingDraft:
        """The lead assigns a rater to a module (creates their empty, unsubmitted draft). Lead/admin
        only; refused on a finalised assessment, an unknown consultant, or a duplicate."""
        row = self._require_assessment(principal, assessment_id)  # owner/admin only
        if row.state == AssessmentState.FINALISED.value:
            raise ConflictError(
                f"Assessment {assessment_id} is finalised; rater assignment is locked (#6)."
            )
        if self._session.get(ConsultantORM, rater_consultant_id) is None:
            raise NotFoundError(f"Consultant {rater_consultant_id} not found.")
        existing = self._session.execute(
            select(ModuleRatingDraftORM.id).where(
                ModuleRatingDraftORM.assessment_id == assessment_id,
                ModuleRatingDraftORM.module_key == module_key,
                ModuleRatingDraftORM.owner_consultant_id == rater_consultant_id,
            )
        ).first()
        if existing is not None:
            raise ConflictError(
                f"Consultant {rater_consultant_id} is already assigned to module {module_key}."
            )
        draft = ModuleRatingDraftORM(
            owner_consultant_id=rater_consultant_id,
            assessment_id=assessment_id,
            module_key=module_key,
            ratings_json="[]",
            submitted=False,
        )
        self._session.add(draft)
        try:
            self._session.flush()
        except IntegrityError as exc:  # a concurrent assign won the unique-constraint race
            self._session.rollback()
            raise ConflictError(
                f"Consultant {rater_consultant_id} is already assigned to module {module_key}."
            ) from exc
        return self._to_module_rating_draft(draft)

    def get_own_module_draft(
        self, principal: Principal, assessment_id: UUID, module_key: str
    ) -> ModuleRatingDraft:
        return self._to_module_rating_draft(
            self._require_own_draft(principal, assessment_id, module_key)
        )

    def update_own_module_draft(
        self,
        principal: Principal,
        assessment_id: UUID,
        module_key: str,
        *,
        ratings: tuple[SubcomponentRating, ...],
    ) -> ModuleRatingDraft:
        """A rater fills in their OWN draft. Refused once submitted (locked) or the assessment is
        finalised. Ratings must all belong to this module (fail loud on a stray module_key)."""
        draft = self._require_own_draft(principal, assessment_id, module_key)
        self._refuse_if_finalised(assessment_id)
        if draft.submitted:
            raise ConflictError(
                "Your rating is submitted and locked; a submitted rating cannot be edited."
            )
        stray = sorted({r.module_key for r in ratings if r.module_key != module_key})
        if stray:
            raise ConflictError(
                f"Every rating must be for module {module_key}; found stray module_key(s) {stray}."
            )
        draft.ratings_json = json.dumps([r.model_dump(mode="json") for r in ratings])
        self._session.add(draft)
        self._session.flush()
        return self._to_module_rating_draft(draft)

    def submit_own_module_draft(
        self, principal: Principal, assessment_id: UUID, module_key: str
    ) -> ModuleRatingDraft:
        """Lock the rater's own draft (blind opens once every assigned rater has submitted). An
        empty draft cannot be submitted — a rater must actually rate at least one subcomponent.
        Refused once the assessment is finalised (its inputs are locked, #6)."""
        draft = self._require_own_draft(principal, assessment_id, module_key)
        self._refuse_if_finalised(assessment_id)
        if draft.submitted:
            raise ConflictError("Your rating is already submitted.")
        if not self._load_ratings(draft.ratings_json):
            raise ConflictError("Cannot submit an empty rating — rate at least one subcomponent.")
        draft.submitted = True
        draft.submitted_at = datetime.now(UTC)
        self._session.add(draft)
        self._session.flush()
        return self._to_module_rating_draft(draft)

    def list_module_drafts(
        self, principal: Principal, assessment_id: UUID, module_key: str
    ) -> list[ModuleRatingDraft]:
        """Blind read: the caller always sees their OWN draft; a co-rater's draft is visible only
        once EVERY assigned rater on the module has submitted. This is the structural guarantee that
        the second opinion is formed independently (Methodology §9) — it holds for the lead and even
        for an admin, because peeking would defeat the method, not merely leak data."""
        self._require_rating_access(principal, assessment_id)
        rows = self._module_drafts(assessment_id, module_key)
        all_submitted = bool(rows) and all(r.submitted for r in rows)
        visible = [
            r for r in rows if r.owner_consultant_id == principal.consultant_id or all_submitted
        ]
        return [self._to_module_rating_draft(r) for r in visible]

    def list_my_rating_assignments(
        self, principal: Principal
    ) -> list[tuple[ModuleRatingDraft, str]]:
        """Every module the caller has been assigned to rate, with the assessment's subject — how a
        co-rater finds the ratings requested of them. Owner-scoped to the caller's own draft rows;
        it never reveals a co-rater's ratings (only that an assignment exists)."""
        stmt = (
            select(ModuleRatingDraftORM, AssessmentORM.subject)
            .join(AssessmentORM, AssessmentORM.id == ModuleRatingDraftORM.assessment_id)
            .where(ModuleRatingDraftORM.owner_consultant_id == principal.consultant_id)
            .where(AssessmentORM.state != AssessmentState.FINALISED.value)
            .order_by(ModuleRatingDraftORM.created_at.desc())
        )
        rows = self._session.execute(stmt).all()
        return [(self._to_module_rating_draft(d), subject) for d, subject in rows]

    def resolve_module_consensus(
        self,
        principal: Principal,
        assessment_id: UUID,
        module_key: str,
        *,
        resolved: tuple[SubcomponentRating, ...],
    ) -> Assessment:
        """The lead records the agreed rating for each assessed subcomponent of a module, drawing on
        the now-visible rater drafts, and it is written into the assessment document. Enforced:
        ≥2 raters assigned and ALL submitted; each resolved subcomponent was assessed by ≥2 raters;
        a subcomponent the raters DISAGREED on carries a dissent note. `rater_ids` and `consensus`
        are computed from the drafts here — never caller-supplied — so the governance record is
        trustworthy. The resolved set REPLACES this module's entries in the document."""
        row = self._require_assessment(principal, assessment_id)  # lead/admin only
        if row.state == AssessmentState.FINALISED.value:
            raise ConflictError(
                f"Assessment {assessment_id} is finalised; consensus is locked (#6)."
            )

        drafts = self._module_drafts(assessment_id, module_key)
        if len(drafts) < 2:
            raise ConflictError(
                f"Module {module_key} has {len(drafts)} rater(s); dual rating requires ≥2 "
                f"(Methodology §9)."
            )
        if not all(d.submitted for d in drafts):
            raise ConflictError(
                "Every assigned rater must submit before consensus can be resolved — the blind "
                "opens only when all ratings are in (Methodology §9)."
            )

        # Per subcomponent: which raters ASSESSED it (gave a level) and the distinct levels given.
        raters_by_sub: dict[str, set[UUID]] = {}
        levels_by_sub: dict[str, set[str]] = {}
        for d in drafts:
            for r in self._load_ratings(d.ratings_json):
                if r.level is None:
                    continue  # a rater's "Not Assessed" is not a second opinion on an assessed sub
                raters_by_sub.setdefault(r.subcomponent_key, set()).add(d.owner_consultant_id)
                levels_by_sub.setdefault(r.subcomponent_key, set()).add(r.level.value)

        out: list[SubcomponentRating] = []
        for r in resolved:
            if r.module_key != module_key:
                raise ConflictError(
                    f"Resolved rating {r.subcomponent_key} is not in module {module_key}."
                )
            if r.level is None:
                raise ConflictError(
                    f"Consensus records ASSESSED subcomponents; {r.subcomponent_key} has no level. "
                    "Leave unassessed subcomponents out — they default to Not Assessed."
                )
            raters = raters_by_sub.get(r.subcomponent_key, set())
            if len(raters) < 2:
                raise ConflictError(
                    f"{module_key}/{r.subcomponent_key} was assessed by {len(raters)} rater(s); a "
                    f"deliverable rating needs two independent assessments (Methodology §9)."
                )
            differed = len(levels_by_sub.get(r.subcomponent_key, set())) > 1
            if differed and r.dissent_note is None:
                raise ConflictError(
                    f"{module_key}/{r.subcomponent_key}: the raters differed — a dissent note is "
                    f"required when one position yields to another (Methodology §9)."
                )
            out.append(
                r.model_copy(
                    update={
                        "rater_ids": tuple(sorted(raters, key=str)),
                        "consensus": not differed,
                        "dissent_note": r.dissent_note if differed else None,
                    }
                )
            )

        doc = AssessmentDocument.model_validate_json(row.document_json)
        kept = tuple(s for s in doc.subcomponents if s.module_key != module_key)
        new_doc = doc.model_copy(update={"subcomponents": (*kept, *out)})
        row.document_json = new_doc.model_dump_json()
        if row.state == AssessmentState.DRAFT.value:
            row.state = AssessmentState.IN_PROGRESS.value
        self._session.add(row)
        self._session.flush()
        return self._to_assessment(row)

    @staticmethod
    def _load_ratings(ratings_json: str) -> tuple[SubcomponentRating, ...]:
        return tuple(SubcomponentRating.model_validate(d) for d in json.loads(ratings_json))

    @staticmethod
    def _to_module_rating_draft(row: ModuleRatingDraftORM) -> ModuleRatingDraft:
        return ModuleRatingDraft(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            assessment_id=row.assessment_id,
            module_key=row.module_key,
            ratings=Repository._load_ratings(row.ratings_json),
            submitted=row.submitted,
            submitted_at=row.submitted_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ------------------------------------------------- Rating Committee (SCOPED, Methodology §8)
    # High-stakes ratings need peer sign-off. The committee QUEUE is visible to the assessment
    # owner (to watch status), a committee member, or an admin; a DECISION may be recorded only by a
    # committee member or admin, and never on their own assessment (peer challenge, ADR-0011). The
    # required-items computation lives in `grassmarket.atlas.committee`; this layer stores calls.

    def _require_committee_view(self, principal: Principal, assessment_id: UUID) -> AssessmentORM:
        row = self._session.get(AssessmentORM, assessment_id)
        if row is None:
            raise NotFoundError(f"Assessment {assessment_id} not found.")
        if (
            principal.is_admin
            or principal.is_committee
            or row.owner_consultant_id == principal.consultant_id
        ):
            return row
        raise ScopeViolationError(
            "Only the assessment owner, a committee member, or an admin may view the committee "
            "queue (data scoping is absolute, CLAUDE.md #9; committee visibility per ADR-0011)."
        )

    def get_assessment_for_committee(self, principal: Principal, assessment_id: UUID) -> Assessment:
        """The assessment as seen by a committee viewer (owner / committee / admin) — so the queue
        endpoint can score its document to derive the high-stakes items."""
        return self._to_assessment(self._require_committee_view(principal, assessment_id))

    def list_committee_decisions(
        self, principal: Principal, assessment_id: UUID
    ) -> list[CommitteeDecision]:
        """Every recorded committee call on an assessment (scoped to owner / committee / admin)."""
        self._require_committee_view(principal, assessment_id)
        stmt = (
            select(CommitteeDecisionORM)
            .where(CommitteeDecisionORM.assessment_id == assessment_id)
            .order_by(CommitteeDecisionORM.created_at)
        )
        rows = self._session.execute(stmt).scalars().all()
        return [self._to_committee_decision(r) for r in rows]

    def decide_committee_item(
        self,
        principal: Principal,
        assessment_id: UUID,
        *,
        item_type: CommitteeItemType,
        item_key: str,
        rating: str,
        status: CommitteeDecisionStatus,
        rationale: str,
        dissent_note: str | None = None,
    ) -> CommitteeDecision:
        """Record (or update) the committee's call on one high-stakes item, at the rating reviewed.
        Committee/admin only, and never on the decider's own assessment (peer challenge, §8);
        refused once the assessment is finalised. Upserts on (assessment, item_type, item_key)."""
        assessment = self._session.get(AssessmentORM, assessment_id)
        if assessment is None:
            raise NotFoundError(f"Assessment {assessment_id} not found.")
        if not (principal.is_committee or principal.is_admin):
            # A non-committee principal has no business at the decision surface — do not reveal it.
            raise ScopeViolationError(
                "Only a Rating Committee member or an admin may record a committee decision (§8)."
            )
        if assessment.owner_consultant_id == principal.consultant_id:
            raise ConflictError(
                "A consultant cannot sign off the high-stakes ratings on their own assessment — "
                "committee review is peer challenge, not self-approval (Methodology §8)."
            )
        if assessment.state == AssessmentState.FINALISED.value:
            raise ConflictError(
                f"Assessment {assessment_id} is finalised; committee decisions are locked (#6)."
            )

        stmt = select(CommitteeDecisionORM).where(
            CommitteeDecisionORM.assessment_id == assessment_id,
            CommitteeDecisionORM.item_type == item_type.value,
            CommitteeDecisionORM.item_key == item_key,
        )
        row = self._session.execute(stmt).scalar_one_or_none()
        now = datetime.now(UTC)
        if row is None:
            row = CommitteeDecisionORM(
                owner_consultant_id=assessment.owner_consultant_id,
                assessment_id=assessment_id,
                item_type=item_type.value,
                item_key=item_key,
            )
        row.rating = rating
        row.status = status.value
        row.rationale = rationale
        row.dissent_note = dissent_note
        row.decided_by_consultant_id = principal.consultant_id
        row.decided_at = now
        self._session.add(row)
        try:
            self._session.flush()
        except IntegrityError as exc:  # two members raced the first decision on the same item
            self._session.rollback()
            raise ConflictError(
                f"A committee decision on {item_type.value} {item_key!r} was recorded "
                f"concurrently; re-read the queue and try again."
            ) from exc
        self.record_audit(
            actor_consultant_id=principal.consultant_id,
            event_type=AuditEventType.COMMITTEE_DECISION,
            resource_type="assessment",
            resource_id=assessment_id,
            detail=f"{item_type.value}:{status.value}",
            now=datetime.now(UTC),
        )
        return self._to_committee_decision(row)

    @staticmethod
    def _to_committee_decision(row: CommitteeDecisionORM) -> CommitteeDecision:
        return CommitteeDecision(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            assessment_id=row.assessment_id,
            item_type=CommitteeItemType(row.item_type),
            item_key=row.item_key,
            rating=row.rating,
            status=CommitteeDecisionStatus(row.status),
            rationale=row.rationale,
            dissent_note=row.dissent_note,
            decided_by_consultant_id=row.decided_by_consultant_id,
            decided_at=row.decided_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ------------------------------------------------- calibration (SCOPED, Methodology §9)
    # A calibration session is shared training content: any consultant may read it and submit their
    # own BLIND rating; only the facilitator (an admin) opens/closes it. The per-anchor coefficients
    # exist only once the session is CLOSED — a rater can never see the distribution before
    # submitting (that would defeat the measurement). Each assessor's rating is owner-scoped.

    def _require_calibration_session(self, session_id: UUID) -> CalibrationSessionORM:
        row = self._session.get(CalibrationSessionORM, session_id)
        if row is None:
            raise NotFoundError(f"Calibration session {session_id} not found.")
        return row

    def create_calibration_session(
        self,
        principal: Principal,
        *,
        title: str,
        vignettes: Sequence[CalibrationVignette],
        opened_at: datetime,
    ) -> CalibrationSession:
        """Open a calibration round. Facilitator = an admin (§9)."""
        if not principal.is_admin:
            raise ScopeViolationError(
                "Only an admin (facilitator) may open a calibration session (Methodology §9)."
            )
        row = CalibrationSessionORM(
            owner_consultant_id=principal.consultant_id,
            title=title,
            status=CalibrationStatus.OPEN.value,
            vignettes_json=json.dumps([v.model_dump(mode="json") for v in vignettes]),
            opened_at=opened_at,
        )
        self._session.add(row)
        self._session.flush()
        return self._to_calibration_session(row)

    def list_calibration_sessions(self, principal: Principal) -> list[CalibrationSession]:
        """Every session — calibration is shared training content, visible org-wide (no client data
        here). The blind is on the RESULTS, not the session's existence."""
        rows = (
            self._session.execute(
                select(CalibrationSessionORM).order_by(CalibrationSessionORM.created_at)
            )
            .scalars()
            .all()
        )
        return [self._to_calibration_session(r) for r in rows]

    def get_calibration_session(self, principal: Principal, session_id: UUID) -> CalibrationSession:
        return self._to_calibration_session(self._require_calibration_session(session_id))

    def submit_calibration_rating(
        self,
        principal: Principal,
        session_id: UUID,
        *,
        entries: Sequence[RatingEntry],
        submitted_at: datetime,
    ) -> CalibrationRating:
        """An assessor submits their own blind rating. Must cover exactly the session's anchors;
        refused once submitted (locked) or once the session is closed."""
        session = self._require_calibration_session(session_id)
        if session.status != CalibrationStatus.OPEN.value:
            raise ConflictError("Calibration session is closed; no more ratings accepted.")
        vignettes = [
            CalibrationVignette.model_validate(v) for v in json.loads(session.vignettes_json)
        ]
        required = {(i, a.subcomponent_key) for i, v in enumerate(vignettes) for a in v.anchors}
        given = {(e.vignette_index, e.subcomponent_key) for e in entries}
        # A set comparison alone would silently accept a duplicate (vignette, anchor) with a
        # different level, then last-wins would drop one at compute — check the count too (#3).
        if len(given) != len(entries) or given != required:
            raise ConflictError(
                "A calibration rating must cover exactly the session's anchors — no missing, "
                "extra, or duplicate entries."
            )

        stmt = select(CalibrationRatingORM).where(
            CalibrationRatingORM.session_id == session_id,
            CalibrationRatingORM.owner_consultant_id == principal.consultant_id,
        )
        row = self._session.execute(stmt).scalar_one_or_none()
        if row is not None and row.submitted:
            raise ConflictError("Your calibration rating is already submitted and locked.")
        if row is None:
            row = CalibrationRatingORM(
                owner_consultant_id=principal.consultant_id, session_id=session_id
            )
        row.entries_json = json.dumps([e.model_dump(mode="json") for e in entries])
        row.submitted = True
        row.submitted_at = submitted_at
        self._session.add(row)
        try:
            self._session.flush()
        except IntegrityError as exc:  # concurrent first submit for the same (session, assessor)
            self._session.rollback()
            raise ConflictError("Your calibration rating was recorded concurrently.") from exc
        return self._to_calibration_rating(row)

    def get_my_calibration_rating(
        self, principal: Principal, session_id: UUID
    ) -> CalibrationRating:
        """The caller's OWN rating for a session (never a co-rater's — that is the blind)."""
        stmt = select(CalibrationRatingORM).where(
            CalibrationRatingORM.session_id == session_id,
            CalibrationRatingORM.owner_consultant_id == principal.consultant_id,
        )
        row = self._session.execute(stmt).scalar_one_or_none()
        if row is None:
            raise NotFoundError("You have not rated this calibration session.")
        return self._to_calibration_rating(row)

    def close_calibration_session(
        self, principal: Principal, session_id: UUID, *, closed_at: datetime
    ) -> CalibrationResult:
        """Close the session and compute the per-anchor agreement from every submitted rating
        (Methodology §9). Facilitator = an admin (same rule as opening); refused if already closed.
        Raises `CalibrationStatsError` (from the compute) if fewer than two assessors submitted."""
        session = self._require_calibration_session(session_id)
        if not principal.is_admin:
            raise ScopeViolationError(
                "Only an admin (facilitator) may close a calibration session (Methodology §9)."
            )
        if session.status == CalibrationStatus.CLOSED.value:
            raise ConflictError("Calibration session is already closed.")

        ratings = [
            self._to_calibration_rating(r)
            for r in self._session.execute(
                select(CalibrationRatingORM).where(CalibrationRatingORM.session_id == session_id)
            )
            .scalars()
            .all()
        ]
        result = compute_calibration_result(
            self._to_calibration_session(session), ratings, computed_at=closed_at
        )
        session.status = CalibrationStatus.CLOSED.value
        session.closed_at = closed_at
        session.results_json = result.model_dump_json()
        self._session.add(session)
        self._session.flush()
        return result

    def get_calibration_result(self, principal: Principal, session_id: UUID) -> CalibrationResult:
        """The computed result of a CLOSED session (visible org-wide once closed). While the session
        is OPEN the result does not exist — refused, so no rater sees it first (§9)."""
        session = self._require_calibration_session(session_id)
        if session.status != CalibrationStatus.CLOSED.value or session.results_json is None:
            raise ConflictError(
                "Calibration results are blind until the session closes (Methodology §9)."
            )
        return CalibrationResult.model_validate_json(session.results_json)

    @staticmethod
    def _to_calibration_session(row: CalibrationSessionORM) -> CalibrationSession:
        return CalibrationSession(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            title=row.title,
            status=CalibrationStatus(row.status),
            vignettes=tuple(
                CalibrationVignette.model_validate(v) for v in json.loads(row.vignettes_json)
            ),
            opened_at=row.opened_at,
            closed_at=row.closed_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_calibration_rating(row: CalibrationRatingORM) -> CalibrationRating:
        return CalibrationRating(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            session_id=row.session_id,
            entries=tuple(RatingEntry.model_validate(e) for e in json.loads(row.entries_json)),
            submitted=row.submitted,
            submitted_at=row.submitted_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ------------------------------------------------ certification ladder (SCOPED, Methodology §9)
    # The ladder is advanced on RECORDED EVIDENCE, never a badge. Evidence is recorded by an admin
    # (trainer/facilitator); promotion checks the state machine and refuses if the evidence is not
    # in; every credit, promotion and admin override is an append-only event. The advisor's LEVEL is
    # kept on their consultant record (the JWT claim); this layer keeps the evidence + audit trail.

    def _require_cert_admin(self, principal: Principal) -> None:
        if not principal.is_admin:
            raise ScopeViolationError(
                "Only an admin may record certification evidence or promote an advisor (§9)."
            )

    def _consultant_level(self, consultant_id: UUID) -> AssessorLevel:
        row = self._session.get(ConsultantORM, consultant_id)
        if row is None:
            raise NotFoundError(f"Consultant {consultant_id} not found.")
        return AssessorLevel(row.assessor_level)

    def _get_or_create_cert_record(self, consultant_id: UUID) -> CertificationRecordORM:
        stmt = select(CertificationRecordORM).where(
            CertificationRecordORM.owner_consultant_id == consultant_id
        )
        row = self._session.execute(stmt).scalar_one_or_none()
        if row is None:
            if self._session.get(ConsultantORM, consultant_id) is None:
                raise NotFoundError(f"Consultant {consultant_id} not found.")
            row = CertificationRecordORM(owner_consultant_id=consultant_id)
            self._session.add(row)
            try:
                self._session.flush()
            except IntegrityError:  # a concurrent first-access created it — re-read the winner
                self._session.rollback()
                row = self._session.execute(stmt).scalar_one()
        return row

    def _append_cert_event(
        self,
        consultant_id: UUID,
        kind: CertificationEventKind,
        recorded_by: UUID,
        occurred_at: datetime,
        *,
        detail: str = "",
        from_level: AssessorLevel | None = None,
        to_level: AssessorLevel | None = None,
        reason: str | None = None,
        cert_subject: str | None = None,
        assessment_id: UUID | None = None,
    ) -> None:
        self._session.add(
            CertificationEventORM(
                owner_consultant_id=consultant_id,
                kind=kind.value,
                detail=detail,
                from_level=from_level.value if from_level else None,
                to_level=to_level.value if to_level else None,
                reason=reason,
                cert_subject=cert_subject,
                assessment_id=assessment_id,
                recorded_by_consultant_id=recorded_by,
                occurred_at=occurred_at,
            )
        )

    def record_coursework(
        self, principal: Principal, advisor_id: UUID, *, occurred_at: datetime
    ) -> CertificationRecord:
        self._require_cert_admin(principal)
        record = self._get_or_create_cert_record(advisor_id)
        record.coursework_complete = True
        self._append_cert_event(
            advisor_id,
            CertificationEventKind.COURSEWORK_COMPLETED,
            principal.consultant_id,
            occurred_at,
        )
        self._session.flush()
        return self._to_certification_record(record)

    def record_exam(
        self, principal: Principal, advisor_id: UUID, *, score: float, occurred_at: datetime
    ) -> CertificationRecord:
        self._require_cert_admin(principal)
        record = self._get_or_create_cert_record(advisor_id)
        record.exam_score = score
        self._append_cert_event(
            advisor_id,
            CertificationEventKind.EXAM_RECORDED,
            principal.consultant_id,
            occurred_at,
            detail=f"score={score}",
        )
        self._session.flush()
        return self._to_certification_record(record)

    def log_shadow_assessment(
        self, principal: Principal, advisor_id: UUID, *, occurred_at: datetime
    ) -> CertificationRecord:
        # A shadow is an admin-recorded credit (a trusted trainer logs each real participation); the
        # count is not tied to a distinct assessment id — that finer accounting is out of scope.
        self._require_cert_admin(principal)
        record = self._get_or_create_cert_record(advisor_id)
        record.shadow_count += 1
        self._append_cert_event(
            advisor_id,
            CertificationEventKind.SHADOW_LOGGED,
            principal.consultant_id,
            occurred_at,
            detail=f"count={record.shadow_count}",
        )
        self._session.flush()
        return self._to_certification_record(record)

    def log_observed_lead(
        self, principal: Principal, advisor_id: UUID, *, occurred_at: datetime
    ) -> CertificationRecord:
        self._require_cert_admin(principal)
        record = self._get_or_create_cert_record(advisor_id)
        record.observed_lead_logged = True
        self._append_cert_event(
            advisor_id,
            CertificationEventKind.OBSERVED_LEAD_LOGGED,
            principal.consultant_id,
            occurred_at,
        )
        self._session.flush()
        return self._to_certification_record(record)

    def record_signoff(
        self, principal: Principal, advisor_id: UUID, *, signer_id: UUID, occurred_at: datetime
    ) -> CertificationRecord:
        """Record a Certified Lead's sign-off of an advisor's observed lead. Admin-recorded; the
        signer must actually be a Certified Lead, and cannot be the advisor (peer sign-off, §9)."""
        self._require_cert_admin(principal)
        if signer_id == advisor_id:
            raise ConflictError("A sign-off must come from another consultant, not the advisor.")
        if self._consultant_level(signer_id) is not AssessorLevel.CERTIFIED_LEAD:
            raise ConflictError("A sign-off must be recorded by a Certified Lead.")
        record = self._get_or_create_cert_record(advisor_id)
        record.observed_lead_signoff_by = signer_id
        self._append_cert_event(
            advisor_id,
            CertificationEventKind.SIGNOFF_RECORDED,
            principal.consultant_id,
            occurred_at,
            detail=f"signer={signer_id}",
        )
        self._session.flush()
        return self._to_certification_record(record)

    def promote_advisor(
        self, principal: Principal, advisor_id: UUID, *, occurred_at: datetime
    ) -> CertificationRecord:
        """Advance an advisor one rung — refused unless the next level's evidence is in (§9)."""
        self._require_cert_admin(principal)
        consultant = self._session.get(ConsultantORM, advisor_id)
        if consultant is None:
            raise NotFoundError(f"Consultant {advisor_id} not found.")
        record = self._get_or_create_cert_record(advisor_id)
        current = AssessorLevel(consultant.assessor_level)
        target = next_level(current)
        if target is None:
            raise ConflictError(f"{current.value} is already the top of the ladder.")
        blockers = promotion_blockers(self._to_certification_record(record), target)
        if blockers:
            raise ConflictError(
                f"Cannot promote to {target.value} — evidence incomplete: " + " ".join(blockers)
            )
        consultant.assessor_level = target
        self._append_cert_event(
            advisor_id,
            CertificationEventKind.PROMOTED,
            principal.consultant_id,
            occurred_at,
            from_level=current,
            to_level=target,
        )
        self._session.add(consultant)
        self._session.flush()
        return self._to_certification_record(record)

    def record_certification_override(
        self,
        principal: Principal,
        advisor_id: UUID,
        *,
        reason: str,
        detail: str,
        occurred_at: datetime,
    ) -> None:
        """Append an admin OVERRIDE audit record (e.g. a certification-gate bypass at finalisation).
        Admin-only and the reason is mandatory — no silent bypass (§9). Self-guarded here (not only
        at the router) because this is the one privileged path that skips a governance gate."""
        self._require_cert_admin(principal)
        if not reason.strip():
            raise ConflictError("An override reason is mandatory — no silent bypass (§9).")
        self._append_cert_event(
            advisor_id,
            CertificationEventKind.OVERRIDE,
            principal.consultant_id,
            occurred_at,
            detail=detail,
            reason=reason,
        )
        self.record_audit(
            actor_consultant_id=principal.consultant_id,
            event_type=AuditEventType.CERTIFICATION_OVERRIDE,
            resource_type="consultant",
            resource_id=advisor_id,
            detail=reason[:200],
            now=occurred_at,
        )
        self._session.flush()

    def get_certification_record(
        self, principal: Principal, advisor_id: UUID
    ) -> CertificationRecord:
        """An advisor's own record, or any advisor's for an admin."""
        if not (principal.is_admin or advisor_id == principal.consultant_id):
            raise ScopeViolationError("You may view only your own certification record.")
        return self._to_certification_record(self._get_or_create_cert_record(advisor_id))

    def list_certification_events(
        self, principal: Principal, advisor_id: UUID
    ) -> list[CertificationEvent]:
        if not (principal.is_admin or advisor_id == principal.consultant_id):
            raise ScopeViolationError("You may view only your own certification history.")
        rows = (
            self._session.execute(
                select(CertificationEventORM)
                .where(CertificationEventORM.owner_consultant_id == advisor_id)
                .order_by(CertificationEventORM.occurred_at, CertificationEventORM.created_at)
            )
            .scalars()
            .all()
        )
        return [self._to_certification_event(r) for r in rows]

    def _to_certification_record(self, row: CertificationRecordORM) -> CertificationRecord:
        return CertificationRecord(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            level=self._consultant_level(row.owner_consultant_id),
            coursework_complete=row.coursework_complete,
            exam_score=row.exam_score,
            shadow_count=row.shadow_count,
            observed_lead_logged=row.observed_lead_logged,
            observed_lead_signoff_by=row.observed_lead_signoff_by,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_certification_event(row: CertificationEventORM) -> CertificationEvent:
        return CertificationEvent(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            kind=CertificationEventKind(row.kind),
            detail=row.detail,
            from_level=AssessorLevel(row.from_level) if row.from_level else None,
            to_level=AssessorLevel(row.to_level) if row.to_level else None,
            reason=row.reason,
            cert_subject=row.cert_subject,
            assessment_id=row.assessment_id,
            recorded_by_consultant_id=row.recorded_by_consultant_id,
            occurred_at=row.occurred_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ------------------------------------------------- course/product certifications (GRS-0127)
    # A Sales Egoist cert + one per product, on top of the assessor ladder. They REUSE the
    # certification-events audit (cert_subject != None) — no parallel store — and need the backing
    # course complete AND a senior sign-off that is not the learner (the senior↔junior pairing).
    def _learner_completed_course(self, advisor_id: UUID, slug: str) -> bool:
        """True iff the advisor has completed every approved lesson of the latest published course
        with this slug. An unpublished/absent course ⟹ not complete (you can't finish what isn't
        there)."""
        course = self._session.execute(
            select(CourseORM).where(CourseORM.slug == slug)
        ).scalar_one_or_none()
        if course is None:
            return False
        latest = self._latest_published_row(course.id)
        if latest is None:
            return False
        tree = CourseTree.model_validate_json(latest.tree_json)
        completed = {
            r.lesson_id
            for r in self._session.execute(
                select(LessonCompletionORM).where(
                    LessonCompletionORM.owner_consultant_id == advisor_id,
                    LessonCompletionORM.course_id == course.id,
                )
            ).scalars()
        }
        return is_course_complete(tree, frozenset(completed))

    def _course_cert_signoff_event(
        self, advisor_id: UUID, subject_key: str
    ) -> CertificationEventORM | None:
        """The advisor's sign-off event for a cert subject, if any (the certifying evidence)."""
        return self._session.execute(
            select(CertificationEventORM)
            .where(
                CertificationEventORM.owner_consultant_id == advisor_id,
                CertificationEventORM.cert_subject == subject_key,
                CertificationEventORM.kind == CertificationEventKind.SIGNOFF_RECORDED.value,
            )
            .order_by(CertificationEventORM.occurred_at)
        ).scalar_one_or_none()

    def _course_certification(
        self, advisor_id: UUID, subject: CourseCertSubject
    ) -> CourseCertification:
        signoff = self._course_cert_signoff_event(advisor_id, subject.key)
        complete = self._learner_completed_course(advisor_id, subject.backing_slug)
        return CourseCertification(
            owner_consultant_id=advisor_id,
            subject=subject.key,
            title=subject.title,
            status=course_cert_status(course_complete=complete, has_signoff=signoff is not None),
            course_complete=complete,
            signed_off_by_consultant_id=(
                signoff.recorded_by_consultant_id if signoff is not None else None
            ),
            certified_at=signoff.occurred_at if signoff is not None else None,
        )

    def _cert_subjects(self) -> list[CourseCertSubject]:
        return course_cert_subjects(load_commission_config().products)

    def list_course_certifications(
        self, principal: Principal, advisor_id: UUID
    ) -> list[CourseCertification]:
        """An advisor's full course/product cert set (self, or any for an admin)."""
        if not (principal.is_admin or advisor_id == principal.consultant_id):
            raise ScopeViolationError("You may view only your own certifications.")
        if self._session.get(ConsultantORM, advisor_id) is None:
            raise NotFoundError(f"Consultant {advisor_id} not found.")
        return [self._course_certification(advisor_id, s) for s in self._cert_subjects()]

    def signoff_course_certification(
        self, principal: Principal, advisor_id: UUID, subject_key: str, *, now: datetime
    ) -> CourseCertification:
        """A senior signs off a junior's course/product cert (GRS-0127) — the pairing.
        Refuses (ConflictError) unless the learner completed the course AND the signer is a
        separate, senior operator (Certified Lead or admin). A second sign-off is refused."""
        subject = next((s for s in self._cert_subjects() if s.key == subject_key), None)
        if subject is None:
            raise NotFoundError(f"Unknown certification subject '{subject_key}'.")
        if self._session.get(ConsultantORM, advisor_id) is None:
            raise NotFoundError(f"Consultant {advisor_id} not found.")

        signer_is_senior = (
            principal.is_admin
            or self._consultant_level(principal.consultant_id) is AssessorLevel.CERTIFIED_LEAD
        )
        blockers = signoff_blockers(
            course_complete=self._learner_completed_course(advisor_id, subject.backing_slug),
            signer_is_senior=signer_is_senior,
            signer_is_learner=principal.consultant_id == advisor_id,
        )
        if blockers:
            raise ConflictError("Cannot sign off this certification: " + "; ".join(blockers))
        if self._course_cert_signoff_event(advisor_id, subject.key) is not None:
            raise ConflictError(f"'{subject.title}' is already certified for this advisor.")

        self._append_cert_event(
            advisor_id,
            CertificationEventKind.SIGNOFF_RECORDED,
            principal.consultant_id,
            now,
            detail=f"course cert: {subject.title}",
            cert_subject=subject.key,
        )
        self._session.flush()
        return self._course_certification(advisor_id, subject)

    # ------------------------------------------------- Power Drills (SCOPED, SM-2, GRS-0024)
    # Each advisor owns their own spaced-repetition cards; answering one reschedules it by SM-2. The
    # clock is injected (never `datetime.now()` inside), so the schedule is deterministic in tests.

    def create_drill_card(
        self,
        principal: Principal,
        *,
        topic: str,
        now: datetime,
        prompt: str = "",
        answer: str = "",
    ) -> DrillCard:
        """Add a drill card for the caller over a topic — due immediately. One card per topic.
        `prompt`/`answer` carry the retrieval content (GRS-0139); empty for a bare topic card."""
        row = DrillCardORM(
            owner_consultant_id=principal.consultant_id,
            topic=topic,
            prompt=prompt,
            answer=answer,
            due_at=now,
        )
        self._session.add(row)
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise ConflictError(f"You already have a drill card for {topic!r}.") from exc
        return self._to_drill_card(row)

    def _has_drill_card(self, advisor_id: UUID, topic: str) -> bool:
        return (
            self._session.execute(
                select(DrillCardORM.id).where(
                    DrillCardORM.owner_consultant_id == advisor_id,
                    DrillCardORM.topic == topic,
                )
            ).first()
            is not None
        )

    def list_drill_cards(self, principal: Principal) -> list[DrillCard]:
        rows = (
            self._session.execute(
                select(DrillCardORM)
                .where(DrillCardORM.owner_consultant_id == principal.consultant_id)
                .order_by(DrillCardORM.due_at)
            )
            .scalars()
            .all()
        )
        return [self._to_drill_card(r) for r in rows]

    def list_due_drill_cards(self, principal: Principal, *, now: datetime) -> list[DrillCard]:
        """The caller's cards that are due for review (due_at ≤ now)."""
        rows = (
            self._session.execute(
                select(DrillCardORM)
                .where(
                    DrillCardORM.owner_consultant_id == principal.consultant_id,
                    DrillCardORM.due_at <= now,
                )
                .order_by(DrillCardORM.due_at)
            )
            .scalars()
            .all()
        )
        return [self._to_drill_card(r) for r in rows]

    def answer_drill_card(
        self, principal: Principal, card_id: UUID, *, grade: int, now: datetime
    ) -> DrillCard:
        """Review the caller's own card at recall-quality `grade` — reschedule by SM-2, update the
        streak (a pass extends it, a lapse resets it), and stamp the review time."""
        row = self._session.get(DrillCardORM, card_id)
        if row is None:
            raise NotFoundError(f"Drill card {card_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)

        new_state = review(
            DrillState(
                repetitions=row.repetitions,
                easiness=row.easiness,
                interval_days=row.interval_days,
            ),
            grade,
        )
        row.repetitions = new_state.repetitions
        row.easiness = new_state.easiness
        row.interval_days = new_state.interval_days
        row.due_at = next_due(now, new_state)
        row.streak = row.streak + 1 if grade >= PASSING_GRADE else 0
        row.last_reviewed_at = now
        self._session.add(row)
        self._session.flush()
        return self._to_drill_card(row)

    # ------------------------------------------------- learning content (feeds certification)
    def create_learning_module(
        self,
        principal: Principal,
        *,
        kind: LearningKind,
        title: str,
        methodology_ref: str,
        certification_credit: CertificationCredit = CertificationCredit.NONE,
    ) -> LearningModule:
        """Author a shared learning module (admin)."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may author learning content (PRD §6).")
        row = LearningModuleORM(
            owner_consultant_id=principal.consultant_id,
            kind=kind.value,
            title=title,
            methodology_ref=methodology_ref,
            certification_credit=certification_credit.value,
        )
        self._session.add(row)
        self._session.flush()
        return self._to_learning_module(row)

    def list_learning_modules(self, principal: Principal) -> list[LearningModule]:
        """All learning modules — shared content, visible org-wide."""
        rows = (
            self._session.execute(select(LearningModuleORM).order_by(LearningModuleORM.created_at))
            .scalars()
            .all()
        )
        return [self._to_learning_module(r) for r in rows]

    def complete_learning_module(
        self, principal: Principal, module_id: UUID, *, score: float | None, now: datetime
    ) -> ContentCompletion:
        """The caller completes a learning module. If the module grants a certification credit, the
        evidence is applied to the caller's certification record and audited — self-service, but
        only for COURSEWORK (binary and platform-verifiable). An exam score is objective and never
        self-attested: the certification exam is proctored/admin-recorded (GRS-0023, ADR-0014). A
        practice-exam `score` is stored on the completion for the advisor's own tracking only. One
        completion per (advisor, module)."""
        module = self._session.get(LearningModuleORM, module_id)
        if module is None:
            raise NotFoundError(f"Learning module {module_id} not found.")
        credit = CertificationCredit(module.certification_credit)

        completion = ContentCompletionORM(
            owner_consultant_id=principal.consultant_id,
            module_id=module_id,
            score=score,
            completed_at=now,
        )
        self._session.add(completion)
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise ConflictError("You have already completed this module.") from exc

        if credit is CertificationCredit.COURSEWORK:
            self._apply_coursework_credit(principal.consultant_id, now)
        return self._to_content_completion(completion)

    def _apply_coursework_credit(self, advisor_id: UUID, now: datetime) -> None:
        """Grant the self-service coursework credit to the advisor's certification record, audited.
        (Never the exam credit — that is proctored/admin-only, GRS-0023.)"""
        record = self._get_or_create_cert_record(advisor_id)
        record.coursework_complete = True
        self._append_cert_event(
            advisor_id,
            CertificationEventKind.COURSEWORK_COMPLETED,
            advisor_id,
            now,
            detail="via learning module",
        )
        self._session.flush()

    # ------------------------------------------------- Academy courses (CMS, GRS-0121)
    # Shared catalog content: authoring is ADMIN-gated (like the weekly quiz), reads are org-wide.
    # The editable draft is a CourseTree stored as JSON; publishing appends an immutable version.
    def create_course(
        self,
        principal: Principal,
        *,
        slug: str,
        title: str,
        summary: str,
        certification_credit: CertificationCredit = CertificationCredit.NONE,
    ) -> Course:
        """Create an empty course (admin). The slug is unique; the draft starts with no modules."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may author courses.")
        draft = CourseTree(title=title, summary=summary, certification_credit=certification_credit)
        row = CourseORM(
            owner_consultant_id=principal.consultant_id,
            slug=slug,
            draft_json=draft.model_dump_json(),
        )
        self._session.add(row)
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise ConflictError(f"A course with slug '{slug}' already exists.") from exc
        return self._to_course(row)

    def _get_course_row(self, slug: str) -> CourseORM:
        row = self._session.execute(
            select(CourseORM).where(CourseORM.slug == slug)
        ).scalar_one_or_none()
        if row is None:
            raise NotFoundError(f"Course '{slug}' not found.")
        return row

    def get_course(self, principal: Principal, slug: str) -> Course:
        """The editable draft (admin) — the authoring view. Learners use the published endpoints."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may view a course draft.")
        return self._to_course(self._get_course_row(slug))

    def list_courses(self, principal: Principal) -> list[Course]:
        """Every course draft (admin), published or not."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may list course drafts.")
        rows = self._session.execute(select(CourseORM).order_by(CourseORM.created_at)).scalars()
        return [self._to_course(r) for r in rows]

    def save_course_draft(self, principal: Principal, slug: str, tree: CourseTree) -> Course:
        """Replace the editable draft tree (admin). Does not publish — publishing is explicit."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may edit a course.")
        row = self._get_course_row(slug)
        row.draft_json = tree.model_dump_json()
        self._session.add(row)
        self._session.flush()
        return self._to_course(row)

    def approve_course_lesson(
        self, principal: Principal, slug: str, lesson_id: UUID, *, now: datetime
    ) -> Course:
        """Approve one AI-authored lesson in the draft (admin) so it can be published (ADR-0009)."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may approve a lesson.")
        row = self._get_course_row(slug)
        tree = CourseTree.model_validate_json(row.draft_json)
        try:
            approved = approve_lesson_in_tree(
                tree, lesson_id, approver_id=principal.consultant_id, now=now
            )
        except KeyError as exc:
            raise NotFoundError(f"Lesson {lesson_id} not in course '{slug}'.") from exc
        row.draft_json = approved.model_dump_json()
        self._session.add(row)
        self._session.flush()
        return self._to_course(row)

    def publish_course(self, principal: Principal, slug: str, *, now: datetime) -> CourseVersion:
        """Snapshot the current draft into a new immutable version (admin). Refuses if any
        AI-authored lesson is still unapproved — AI content never reaches a learner ungated
        (ADR-0009)."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may publish a course.")
        row = self._get_course_row(slug)
        tree = CourseTree.model_validate_json(row.draft_json)
        blockers = unapproved_ai_lessons(tree)
        if blockers:
            raise ConflictError(
                "Cannot publish — these AI-authored lessons need approval first (ADR-0009): "
                + ", ".join(blockers)
            )
        self._refuse_duplicate_section_order(slug, tree)
        self._refuse_duplicate_section_id(slug, tree)
        version = row.latest_version + 1
        snapshot = CourseVersionORM(
            course_id=row.id,
            slug=row.slug,
            version=version,
            tree_json=row.draft_json,
            published_by_consultant_id=principal.consultant_id,
            published_at=now,
        )
        row.latest_version = version
        self._session.add_all([snapshot, row])
        self._session.flush()
        return self._to_course_version(snapshot)

    @staticmethod
    def _refuse_duplicate_section_order(slug: str, tree: CourseTree) -> None:
        """A course whose sections share an `order` cannot be published.

        `section_progress` walks the sections in `order` to decide what is unlocked, so two
        sections holding the same number make the gate ambiguous: whichever the sort happened to
        put second inherits the first's standing and opens without being earned. That is the
        unlock rule quietly failing open, which is exactly what a gate must never do — so it is
        refused here, at the one point every tree passes through, rather than sorted around."""
        seen: dict[int, str] = {}
        collisions: list[str] = []
        for module in tree.modules:
            if module.order in seen:
                collisions.append(
                    f"section {module.order} is claimed by both {seen[module.order]!r} "
                    f"and {module.title!r}"
                )
            else:
                seen[module.order] = module.title
        if collisions:
            raise ConflictError(
                f"Cannot publish '{slug}' — its sections do not have distinct order numbers, so "
                "the unlock gate would be ambiguous: " + "; ".join(collisions)
            )

    @staticmethod
    def _refuse_duplicate_section_id(slug: str, tree: CourseTree) -> None:
        """A course with two sections sharing a module id cannot be published.

        Sibling rule to the order check, and found the same way: a course tree assembled from more
        than one source derives its ids by hashing a key, and two sources using the same key produce
        the same id. `record_section_test_attempt` and `section_progress` both key by module id, so
        a duplicate makes one advisor's attempt count for two sections and makes the reader match
        whichever the sort reached first. An id is the record's identity; it cannot be shared."""
        seen: dict[UUID, str] = {}
        collisions: list[str] = []
        for module in tree.modules:
            if module.id in seen:
                collisions.append(
                    f"{module.id} is claimed by both {seen[module.id]!r} and {module.title!r}"
                )
            else:
                seen[module.id] = module.title
        if collisions:
            raise ConflictError(
                f"Cannot publish '{slug}' — two or more sections share an id, so an attempt "
                "recorded against one would count for both: " + "; ".join(collisions)
            )

    def _latest_published_row(self, course_id: UUID) -> CourseVersionORM | None:
        return (
            self._session.execute(
                select(CourseVersionORM)
                .where(CourseVersionORM.course_id == course_id)
                .order_by(CourseVersionORM.version.desc())
            )
            .scalars()
            .first()
        )

    def list_published_courses(self, principal: Principal) -> list[CourseVersion]:
        """The latest published version of every course — the learner-facing catalog (org-wide). The
        mandatory-first course (GRS-0122) sorts to the front so a new advisor's path opens on it;
        the rest keep creation order."""
        courses = self._session.execute(select(CourseORM).order_by(CourseORM.created_at)).scalars()
        out: list[CourseVersion] = []
        for course in courses:
            latest = self._latest_published_row(course.id)
            if latest is not None:
                out.append(self._to_course_version(latest))
        # Stable sort: mandatory-first first, otherwise preserve creation order.
        out.sort(key=lambda v: 0 if v.tree.mandatory_first else 1)
        return out

    def _next_academy_course_title(self, principal: Principal) -> str | None:
        """The title of the next published course the advisor has not completed — mandatory-first
        first (they sort to the front). None when the catalogue is empty or all done (GRS-0128)."""
        for published in self.list_published_courses(principal):
            if not self._learner_completed_course(principal.consultant_id, published.slug):
                return published.tree.title
        return None

    def upsert_published_course(
        self, principal: Principal, slug: str, tree: CourseTree, *, now: datetime
    ) -> CourseVersion:
        """Idempotently seed a course (admin): create it if the slug is new, else replace its draft,
        then publish. Re-running produces a fresh retained version with identical content — the seed
        is safe to apply on every boot (GRS-0122)."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may seed a course.")
        existing = self._session.execute(
            select(CourseORM).where(CourseORM.slug == slug)
        ).scalar_one_or_none()
        if existing is None:
            self.create_course(
                principal,
                slug=slug,
                title=tree.title,
                summary=tree.summary,
                certification_credit=tree.certification_credit,
            )
        self.save_course_draft(principal, slug, tree)
        return self.publish_course(principal, slug, now=now)

    def get_published_course(self, principal: Principal, slug: str) -> CourseVersion:
        """The latest published version of one course (org-wide). 404 if never published."""
        row = self._get_course_row(slug)
        latest = self._latest_published_row(row.id)
        if latest is None:
            raise NotFoundError(f"Course '{slug}' has no published version.")
        return self._to_course_version(latest)

    def list_course_versions(self, principal: Principal, slug: str) -> list[CourseVersion]:
        """Every published version of a course, oldest first (admin) — the retained history."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may list course versions.")
        row = self._get_course_row(slug)
        versions = self._session.execute(
            select(CourseVersionORM)
            .where(CourseVersionORM.course_id == row.id)
            .order_by(CourseVersionORM.version)
        ).scalars()
        return [self._to_course_version(v) for v in versions]

    def complete_lesson(
        self, principal: Principal, slug: str, lesson_id: UUID, *, now: datetime
    ) -> LessonCompletion:
        """The caller completes one lesson of the latest published course. When they have completed
        every approved lesson of a COURSEWORK-credit course, the coursework credit is applied via
        the SAME certification path a learning module uses (no regression). One completion per
        (advisor, lesson)."""
        published = self.get_published_course(principal, slug)  # 404 if never published
        course = self._get_course_row(slug)
        approved_ids = {lesson.id for module in published.tree.modules for lesson in module.lessons}
        # (approved_lesson_ids over the published tree — every lesson in a published version is
        # approved, since publish gated on it.)
        if lesson_id not in approved_ids:
            raise NotFoundError(f"Lesson {lesson_id} is not in the published course '{slug}'.")

        completion = LessonCompletionORM(
            owner_consultant_id=principal.consultant_id,
            course_id=course.id,
            lesson_id=lesson_id,
            completed_at=now,
        )
        self._session.add(completion)
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise ConflictError("You have already completed this lesson.") from exc

        # Wire the spaced-repetition loop (GRS-0139): completing a lesson auto-enrolls a real drill
        # card — with a recall question + model answer — for each topic it teaches, so learning is
        # reinforced, not read-and-forget. Idempotent: skip a topic the advisor already drills.
        lesson = next(
            (les for m in published.tree.modules for les in m.lessons if les.id == lesson_id),
            None,
        )
        if lesson is not None:
            prompt, answer = self._lesson_drill_content(lesson)
            for topic in lesson.drill_topics:
                if not self._has_drill_card(principal.consultant_id, topic):
                    self.create_drill_card(
                        principal, topic=topic, now=now, prompt=prompt, answer=answer
                    )

        completed = {
            r.lesson_id
            for r in self._session.execute(
                select(LessonCompletionORM).where(
                    LessonCompletionORM.owner_consultant_id == principal.consultant_id,
                    LessonCompletionORM.course_id == course.id,
                )
            ).scalars()
        }
        if (
            published.tree.certification_credit is CertificationCredit.COURSEWORK
            and is_course_complete(published.tree, frozenset(completed))
        ):
            self._apply_coursework_credit(principal.consultant_id, now)
        return self._to_lesson_completion(completion)

    def list_lesson_completions(self, principal: Principal, slug: str) -> list[LessonCompletion]:
        """The caller's OWN lesson completions for a published course, so the learner reader shows
        progress and never re-POSTs a done lesson. Owner-scoped (a consultant sees only their own
        progress); the course is org-wide readable. 404 if the course was never published."""
        self.get_published_course(principal, slug)  # 404 if never published
        course = self._get_course_row(slug)
        rows = self._session.execute(
            select(LessonCompletionORM)
            .where(
                LessonCompletionORM.owner_consultant_id == principal.consultant_id,
                LessonCompletionORM.course_id == course.id,
            )
            .order_by(LessonCompletionORM.completed_at)
        ).scalars()
        return [self._to_lesson_completion(r) for r in rows]

    def record_section_test_attempt(
        self,
        principal: Principal,
        slug: str,
        module_id: UUID,
        answers: Sequence[int],
        *,
        now: datetime,
    ) -> SectionTestAttempt:
        """Mark one attempt at one section's test and record it (GRS-0226).

        The caller sends the options they chose; the score is computed here from the PUBLISHED
        tree. A client never asserts its own result. Append-only — a retake is a new row, so the
        record shows how many goes it took.

        Fail loud: a wrong number of answers is refused rather than padded or truncated, because
        either would silently mark a question the advisor never saw."""
        published = self.get_published_course(principal, slug)  # 404 if never published
        course = self._get_course_row(slug)
        module = next((m for m in published.tree.modules if m.id == module_id), None)
        if module is None:
            raise NotFoundError(f"Section {module_id} is not in the published course '{slug}'.")
        test = module.section_test
        if test is None:
            raise NotFoundError(f"Section {module.title!r} has no test to attempt.")
        if len(answers) != len(test.questions):
            raise ConflictError(
                f"This test has {len(test.questions)} question(s) and {len(answers)} answer(s) "
                "were sent; answer every question."
            )
        # A locked section's test cannot be sat. The reader already hides it, but the rule belongs
        # here too: the attempt record is the auditable one, and a row showing section 5 passed
        # before section 1 was opened would describe a progression that never happened.
        standing = next(
            (p for p in self.section_progress(principal, slug) if p.module_id == module_id), None
        )
        if standing is not None and not standing.unlocked:
            raise ConflictError(
                f"Section {module.title!r} is locked — pass the previous section's test first."
            )
        correct = sum(
            1 for q, a in zip(test.questions, answers, strict=True) if a == q.answer_index
        )
        score = correct / len(test.questions)
        attempt = SectionTestAttemptORM(
            owner_consultant_id=principal.consultant_id,
            course_id=course.id,
            module_id=module_id,
            score=score,
            passed=score >= test.pass_mark,
            attempted_at=now,
        )
        self._session.add(attempt)
        self._session.flush()
        return self._to_section_test_attempt(attempt)

    def list_section_test_attempts(
        self, principal: Principal, slug: str
    ) -> list[SectionTestAttempt]:
        """The caller's OWN attempts on one published course, oldest first. Owner-scoped: the
        course is org-wide readable, a colleague's attempts are not."""
        self.get_published_course(principal, slug)  # 404 if never published
        course = self._get_course_row(slug)
        rows = self._session.execute(
            select(SectionTestAttemptORM)
            .where(
                SectionTestAttemptORM.owner_consultant_id == principal.consultant_id,
                SectionTestAttemptORM.course_id == course.id,
            )
            .order_by(SectionTestAttemptORM.attempted_at)
        ).scalars()
        return [self._to_section_test_attempt(r) for r in rows]

    def section_progress(self, principal: Principal, slug: str) -> list[SectionProgress]:
        """The caller's standing on every section of a published course, in section order.

        The unlock rule is stated here and nowhere else: the first section is always open, and a
        later one opens when the section before it has been passed. A section with no test never
        gates — a legacy course must stay readable — so it opens whatever came before it."""
        published = self.get_published_course(principal, slug)  # 404 if never published
        attempts = self.list_section_test_attempts(principal, slug)
        by_module: dict[UUID, list[SectionTestAttempt]] = {}
        for attempt in attempts:
            by_module.setdefault(attempt.module_id, []).append(attempt)

        progress: list[SectionProgress] = []
        previous_clears = True  # nothing precedes the first section, so it is open
        for module in sorted(published.tree.modules, key=lambda m: m.order):
            mine = by_module.get(module.id, [])
            passed = any(a.passed for a in mine)
            has_test = module.section_test is not None
            progress.append(
                SectionProgress(
                    module_id=module.id,
                    order=module.order,
                    has_test=has_test,
                    unlocked=previous_clears,
                    passed=passed,
                    best_score=max((a.score for a in mine), default=None),
                    attempts=len(mine),
                )
            )
            # An untested section cannot gate what follows it; a tested one does.
            previous_clears = previous_clears and (passed or not has_test)
        return progress

    @staticmethod
    def _to_section_test_attempt(row: SectionTestAttemptORM) -> SectionTestAttempt:
        return SectionTestAttempt(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            course_id=row.course_id,
            module_id=row.module_id,
            score=row.score,
            passed=row.passed,
            attempted_at=row.attempted_at,
            # Append-only — an attempt is never mutated, so updated == created.
            created_at=row.created_at,
            updated_at=row.created_at,
        )

    @staticmethod
    def _to_course(row: CourseORM) -> Course:
        return Course(
            id=row.id,
            slug=row.slug,
            draft=CourseTree.model_validate_json(row.draft_json),
            latest_version=row.latest_version,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_course_version(row: CourseVersionORM) -> CourseVersion:
        return CourseVersion(
            course_id=row.course_id,
            slug=row.slug,
            version=row.version,
            tree=CourseTree.model_validate_json(row.tree_json),
            published_by_consultant_id=row.published_by_consultant_id,
            published_at=row.published_at,
        )

    @staticmethod
    def _to_lesson_completion(row: LessonCompletionORM) -> LessonCompletion:
        return LessonCompletion(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            course_id=row.course_id,
            lesson_id=row.lesson_id,
            completed_at=row.completed_at,
            # Append-only — a completion is never mutated, so updated == created.
            created_at=row.created_at,
            updated_at=row.created_at,
        )

    # ------------------------------------------------- the weekly quiz (AI-drafted, gated, #8)
    def propose_quiz(
        self,
        principal: Principal,
        *,
        title: str,
        questions: Sequence[QuizQuestion],
        drafter_version: str,
    ) -> GeneratedQuiz:
        """Store an AI-drafted quiz as a PROPOSAL (admin). Never advisor-visible until approved."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may propose a weekly quiz.")
        row = GeneratedQuizORM(
            owner_consultant_id=principal.consultant_id,
            title=title,
            status=QuizStatus.PROPOSED.value,
            questions_json=json.dumps([q.model_dump(mode="json") for q in questions]),
            drafter_version=drafter_version,
        )
        self._session.add(row)
        self._session.flush()
        return self._to_generated_quiz(row)

    def decide_quiz(
        self, principal: Principal, quiz_id: UUID, *, approve: bool, now: datetime
    ) -> GeneratedQuiz:
        """Approve or reject a proposed quiz (admin). Approval makes it advisor-visible (#8)."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may approve or reject a quiz.")
        row = self._session.get(GeneratedQuizORM, quiz_id)
        if row is None:
            raise NotFoundError(f"Quiz {quiz_id} not found.")
        if row.status != QuizStatus.PROPOSED.value:
            raise ConflictError(f"Quiz {quiz_id} is already {row.status}.")
        if approve:
            row.status = QuizStatus.APPROVED.value
            row.approved_by_consultant_id = principal.consultant_id
            row.approved_at = now
        else:
            row.status = QuizStatus.REJECTED.value
        self._session.add(row)
        self._session.flush()
        return self._to_generated_quiz(row)

    def list_quizzes(self, principal: Principal) -> list[GeneratedQuiz]:
        """An admin sees every quiz; an advisor sees ONLY approved ones — unapproved AI content
        never reaches an advisor (#8)."""
        stmt = select(GeneratedQuizORM)
        if not principal.is_admin:
            stmt = stmt.where(GeneratedQuizORM.status == QuizStatus.APPROVED.value)
        rows = self._session.execute(stmt.order_by(GeneratedQuizORM.created_at)).scalars().all()
        return [self._to_generated_quiz(r) for r in rows]

    def get_quiz(self, principal: Principal, quiz_id: UUID) -> GeneratedQuiz:
        row = self._session.get(GeneratedQuizORM, quiz_id)
        if row is None:
            raise NotFoundError(f"Quiz {quiz_id} not found.")
        # A non-admin may only reach an APPROVED quiz — an unapproved one is hidden (#8).
        if not principal.is_admin and row.status != QuizStatus.APPROVED.value:
            raise NotFoundError(f"Quiz {quiz_id} not found.")
        return self._to_generated_quiz(row)

    @staticmethod
    def _lesson_drill_content(lesson: Lesson) -> tuple[str, str]:
        """The recall question + model answer a completed lesson seeds its drills with (GRS-0139).
        Prefer the authored comprehension check; otherwise derive a recall prompt from the lesson's
        `measurement` (its 'how you know you applied it' criterion), which is the answer key too."""
        if lesson.check_question:
            return lesson.check_question, (lesson.check_answer or lesson.measurement or "")
        if lesson.measurement:
            return (
                f"Recall — {lesson.title}: how do you know you've applied it?",
                lesson.measurement,
            )
        return f"Recall the key idea of '{lesson.title}'.", ""

    @staticmethod
    def _to_drill_card(row: DrillCardORM) -> DrillCard:
        return DrillCard(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            topic=row.topic,
            prompt=row.prompt,
            answer=row.answer,
            repetitions=row.repetitions,
            easiness=row.easiness,
            interval_days=row.interval_days,
            due_at=row.due_at,
            streak=row.streak,
            last_reviewed_at=row.last_reviewed_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_learning_module(row: LearningModuleORM) -> LearningModule:
        return LearningModule(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            kind=LearningKind(row.kind),
            title=row.title,
            methodology_ref=row.methodology_ref,
            certification_credit=CertificationCredit(row.certification_credit),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_content_completion(row: ContentCompletionORM) -> ContentCompletion:
        return ContentCompletion(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            module_id=row.module_id,
            score=row.score,
            completed_at=row.completed_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_generated_quiz(row: GeneratedQuizORM) -> GeneratedQuiz:
        return GeneratedQuiz(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            title=row.title,
            status=QuizStatus(row.status),
            questions=tuple(QuizQuestion.model_validate(q) for q in json.loads(row.questions_json)),
            drafter_version=row.drafter_version,
            approved_by_consultant_id=row.approved_by_consultant_id,
            approved_at=row.approved_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ------------------------------------------------- Practice Arena (SCOPED, GRS-0025, PRD §6)
    # Scenarios are shared, admin-authored content; a session is an advisor's own run — scored
    # deterministically on submit, with AI-drafted (labelled) feedback. No client data — vignettes
    # only. Scores persist to the advisor's own history.

    def create_arena_scenario(
        self,
        principal: Principal,
        *,
        title: str,
        brief: str,
        client_persona: str,
        target_powers: Sequence[ArenaPowerTarget],
        target_modules: Sequence[ArenaModuleTarget] = (),
        evidence_cues: Sequence[str] = (),
    ) -> ArenaScenario:
        """Author a shared Practice Arena scenario (admin)."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may author Practice Arena scenarios (PRD §6).")
        row = ArenaScenarioORM(
            owner_consultant_id=principal.consultant_id,
            title=title,
            brief=brief,
            client_persona=client_persona,
            targets_json=json.dumps(
                {
                    "target_powers": [p.model_dump(mode="json") for p in target_powers],
                    "target_modules": [m.model_dump(mode="json") for m in target_modules],
                    "evidence_cues": list(evidence_cues),
                }
            ),
        )
        self._session.add(row)
        self._session.flush()
        return self._to_arena_scenario(row)

    def list_arena_scenarios(self, principal: Principal) -> list[ArenaScenario]:
        rows = (
            self._session.execute(select(ArenaScenarioORM).order_by(ArenaScenarioORM.created_at))
            .scalars()
            .all()
        )
        return [self._to_arena_scenario(r) for r in rows]

    def get_arena_scenario(self, principal: Principal, scenario_id: UUID) -> ArenaScenario:
        row = self._session.get(ArenaScenarioORM, scenario_id)
        if row is None:
            raise NotFoundError(f"Arena scenario {scenario_id} not found.")
        return self._to_arena_scenario(row)

    def start_arena_session(self, principal: Principal, scenario_id: UUID) -> ArenaSession:
        """Begin a practice session for the caller against a scenario (empty, in progress)."""
        if self._session.get(ArenaScenarioORM, scenario_id) is None:
            raise NotFoundError(f"Arena scenario {scenario_id} not found.")
        row = ArenaSessionORM(
            owner_consultant_id=principal.consultant_id,
            scenario_id=scenario_id,
            status=ArenaStatus.IN_PROGRESS.value,
        )
        self._session.add(row)
        self._session.flush()
        return self._to_arena_session(row)

    def submit_arena_session(
        self,
        principal: Principal,
        session_id: UUID,
        *,
        transcript: Sequence[ArenaTurn],
        drafter: ArenaFeedbackDrafter,
        now: datetime,
    ) -> ArenaSession:
        """Submit the caller's transcript — scored deterministically against the scenario's targets,
        with AI-drafted (labelled) coaching feedback. The score persists to the advisor's history.
        The caller's own session only; refused once already scored."""
        row = self._session.get(ArenaSessionORM, session_id)
        if row is None:
            raise NotFoundError(f"Arena session {session_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        if row.status != ArenaStatus.IN_PROGRESS.value:
            raise ConflictError("This session has already been scored.")

        scenario_row = self._session.get(ArenaScenarioORM, row.scenario_id)
        if scenario_row is None:  # the scenario was deleted out from under the session — fail loud
            raise NotFoundError(f"Arena scenario {row.scenario_id} not found.")
        scenario = self._to_arena_scenario(scenario_row)
        score = score_transcript(scenario, transcript)
        feedback = drafter.draft(scenario, score)

        row.transcript_json = json.dumps([t.model_dump(mode="json") for t in transcript])
        row.score_json = score.model_dump_json()
        row.feedback = feedback
        row.feedback_is_ai_drafted = True
        row.drafter_version = drafter.version
        row.status = ArenaStatus.SCORED.value
        row.scored_at = now
        self._session.add(row)
        self._session.flush()
        return self._to_arena_session(row)

    def list_arena_sessions(self, principal: Principal) -> list[ArenaSession]:
        """The caller's own Practice Arena history (their scores over time)."""
        rows = (
            self._session.execute(
                select(ArenaSessionORM)
                .where(ArenaSessionORM.owner_consultant_id == principal.consultant_id)
                .order_by(ArenaSessionORM.created_at)
            )
            .scalars()
            .all()
        )
        return [self._to_arena_session(r) for r in rows]

    def get_arena_session(self, principal: Principal, session_id: UUID) -> ArenaSession:
        row = self._session.get(ArenaSessionORM, session_id)
        if row is None:
            raise NotFoundError(f"Arena session {session_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        return self._to_arena_session(row)

    @staticmethod
    def _to_arena_scenario(row: ArenaScenarioORM) -> ArenaScenario:
        targets = json.loads(row.targets_json)
        return ArenaScenario(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            title=row.title,
            brief=row.brief,
            client_persona=row.client_persona,
            target_powers=tuple(
                ArenaPowerTarget.model_validate(p) for p in targets["target_powers"]
            ),
            target_modules=tuple(
                ArenaModuleTarget.model_validate(m) for m in targets["target_modules"]
            ),
            evidence_cues=tuple(targets["evidence_cues"]),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_arena_session(row: ArenaSessionORM) -> ArenaSession:
        return ArenaSession(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            scenario_id=row.scenario_id,
            status=ArenaStatus(row.status),
            transcript=tuple(ArenaTurn.model_validate(t) for t in json.loads(row.transcript_json)),
            score=ArenaScore.model_validate_json(row.score_json) if row.score_json else None,
            feedback=row.feedback,
            feedback_is_ai_drafted=row.feedback_is_ai_drafted,
            drafter_version=row.drafter_version,
            scored_at=row.scored_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ------------------------------------------------- bench queue + performance (GRS-0026, SCOPED)
    def _own_prospects(self, consultant_id: UUID) -> list[Prospect]:
        """The consultant's OWN prospects — strictly owner-scoped, no admin-sees-all branch. The
        bench views are self-only for everyone (ADR-0016), so they must not borrow the admin-aware
        list_prospects, which would otherwise fold the whole org's pipeline into an admin's view."""
        rows = (
            self._session.execute(
                select(ProspectORM)
                .where(ProspectORM.owner_consultant_id == consultant_id)
                .order_by(ProspectORM.created_at)
            )
            .scalars()
            .all()
        )
        return [self._to_prospect(r) for r in rows]

    def _own_engagement_statuses(self, consultant_id: UUID) -> list[str]:
        """The status values of the consultant's OWN engagements — strictly owner-scoped (see
        _own_prospects for why this does not reuse the admin-aware list_engagements)."""
        return list(
            self._session.execute(
                select(EngagementORM.status).where(
                    EngagementORM.owner_consultant_id == consultant_id
                )
            )
            .scalars()
            .all()
        )

    def list_content_completions(self, principal: Principal) -> list[ContentCompletion]:
        """The caller's own learning-module completions."""
        rows = (
            self._session.execute(
                select(ContentCompletionORM)
                .where(ContentCompletionORM.owner_consultant_id == principal.consultant_id)
                .order_by(ContentCompletionORM.completed_at)
            )
            .scalars()
            .all()
        )
        return [self._to_content_completion(r) for r in rows]

    def get_bench_queue(self, principal: Principal, *, now: datetime) -> BenchQueue:
        """The caller's prioritised bench-time queue — recomputed from their own workbench state
        (certification, due drills, arena scenarios, early-stage pipeline). Never persisted."""
        cert_record = self._to_certification_record(
            self._get_or_create_cert_record(principal.consultant_id)
        )
        completed_ids = frozenset(c.module_id for c in self.list_content_completions(principal))
        next_coursework = pick_next_coursework(self.list_learning_modules(principal), completed_ids)
        due_drills = self.list_due_drill_cards(principal, now=now)
        arena_scenario = pick_arena_scenario(
            self.list_arena_scenarios(principal), self.list_arena_sessions(principal)
        )
        research_prospect = pick_research_prospect(self._own_prospects(principal.consultant_id))

        # GRS-0128 folded the Academy into the one hub. The peer-governance reads that used to sit
        # here (rating assignments, the committee queue) went with ADR-0041: nobody is blocked on a
        # peer any more, so nothing about them belongs in an advisor's bench.
        academy_title = self._next_academy_course_title(principal)

        items = assemble_queue(
            cert_record=cert_record,
            next_coursework=next_coursework,
            due_drills=due_drills,
            arena_scenario=arena_scenario,
            research_prospect=research_prospect,
            academy_course_title=academy_title,
        )
        return BenchQueue(
            owner_consultant_id=principal.consultant_id, generated_at=now, items=items
        )

    def get_performance_summary(
        self, principal: Principal, advisor_id: UUID, *, now: datetime
    ) -> PerformanceSummary:
        """An advisor's own development picture. Self only — the cross-advisor/admin aggregate is
        Holy Corner scope (not this ticket), so a foreign id is a 404 (not shown to exist), even
        for an admin."""
        if advisor_id != principal.consultant_id:
            raise NotFoundError(f"Performance summary {advisor_id} not found.")
        cert_record = self._to_certification_record(
            self._get_or_create_cert_record(principal.consultant_id)
        )
        engagement_statuses = self._own_engagement_statuses(principal.consultant_id)
        prospects = self._own_prospects(principal.consultant_id)
        drill_cards = self.list_drill_cards(principal)
        due_drills = self.list_due_drill_cards(principal, now=now)
        return summarise_performance(
            owner_consultant_id=principal.consultant_id,
            cert_record=cert_record,
            engagement_statuses=engagement_statuses,
            prospect_stages=[p.stage for p in prospects],
            due_drill_count=len(due_drills),
            drill_streaks=[c.streak for c in drill_cards],
            arena_sessions=self.list_arena_sessions(principal),
        )

    # ------------------------------------------------------------------ mappers
    @staticmethod
    def _to_scoring_run(row: ScoringRunORM) -> ScoringRun:
        return ScoringRun(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            assessment_id=row.assessment_id,
            engine_version=row.engine_version,
            methodology_version=row.methodology_version,
            coefficient_version=row.coefficient_version,
            uncertainty_version=row.uncertainty_version,
            content_hash=row.content_hash,
            finalised=row.finalised,
            v_index=row.v_index,
            v_p10=row.v_p10,
            v_p90=row.v_p90,
            uncertainty_rating=(
                UncertaintyRating(row.uncertainty_rating) if row.uncertainty_rating else None
            ),
            created_at=row.created_at,
            updated_at=row.created_at,  # immutable — updated == created (there are no updates)
        )

    @staticmethod
    def _to_stored_consultant(row: ConsultantORM) -> StoredConsultant:
        return StoredConsultant(
            id=row.id,
            email=row.email,
            full_name=row.full_name,
            hashed_password=row.hashed_password,
            role=Role(row.role),
            tier=ConsultantTier(row.tier),
            assessor_level=AssessorLevel(row.assessor_level),
            is_active=row.is_active,
            created_at=row.created_at,
            updated_at=row.updated_at,
            google_sub=row.google_sub,
        )

    def bind_google_sub(self, consultant_id: UUID, google_sub: str) -> None:
        """Bind a verified Google account id to a consultant on first Google sign-in (ADR-0024).
        Idempotent when already bound to the SAME sub; a DIFFERENT sub for the same account is
        refused loud (a distinct Google identity must not silently take over an account)."""
        row = self._session.get(ConsultantORM, consultant_id)
        if row is None:
            raise NotFoundError(f"Consultant {consultant_id} not found.")
        if row.google_sub is not None and row.google_sub != google_sub:
            raise ConflictError("This account is already bound to a different Google identity.")
        if row.google_sub is None:
            row.google_sub = google_sub
            self._session.add(row)
            self._session.flush()

    # ------------------------------------------------------------------ login hand-off (UNSCOPED)
    def create_login_handoff_code(
        self, *, consultant_id: UUID, code_hash: str, expires_at: datetime
    ) -> None:
        """Store a single-use hand-off code (its hash only) bound to a consultant (GRS-0074)."""
        self._session.add(
            LoginHandoffCodeORM(
                code_hash=code_hash, consultant_id=consultant_id, expires_at=expires_at
            )
        )
        self._session.flush()

    def consume_login_handoff_code(self, *, code_hash: str, now: datetime) -> UUID:
        """Redeem a hand-off code → the bound consultant id. Fail loud on unknown / already-consumed
        / expired, and mark it consumed so a second exchange is refused (single-use, mirrors the
        invitation single-use logic)."""
        row = self._session.execute(
            select(LoginHandoffCodeORM).where(LoginHandoffCodeORM.code_hash == code_hash)
        ).scalar_one_or_none()
        if row is None:
            raise NotFoundError("Unknown login hand-off code.")
        if row.consumed_at is not None:
            raise ConflictError("Login hand-off code has already been used.")
        expires_at = row.expires_at
        if expires_at.tzinfo is None:  # SQLite may return naive datetimes
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < now:
            raise ConflictError("Login hand-off code has expired.")
        row.consumed_at = now
        self._session.add(row)
        self._session.flush()
        return row.consultant_id

    # ---------------------------------------------------------- refresh tokens (GRS-0120)
    def create_refresh_token(
        self, *, consultant_id: UUID, token_hash: str, expires_at: datetime
    ) -> None:
        """Store a single-use refresh token (its hash only) bound to a consultant (GRS-0120)."""
        self._session.add(
            RefreshTokenORM(
                token_hash=token_hash, consultant_id=consultant_id, expires_at=expires_at
            )
        )
        self._session.flush()

    def rotate_refresh_token(self, *, token_hash: str, now: datetime) -> UUID:
        """Redeem a refresh token → the bound consultant id, marking it consumed so the SAME
        never be replayed (rotation: the caller mints a fresh token to replace it). Fail loud on
        unknown / already-consumed / revoked / expired — a reused refresh token is a hard refusal,
        a silent re-auth (mirrors the hand-off code single-use logic)."""
        row = self._session.execute(
            select(RefreshTokenORM).where(RefreshTokenORM.token_hash == token_hash)
        ).scalar_one_or_none()
        if row is None:
            raise NotFoundError("Unknown refresh token.")
        if row.consumed_at is not None:
            raise ConflictError("Refresh token has already been used.")
        if row.revoked_at is not None:
            raise ConflictError("Refresh token has been revoked.")
        expires_at = row.expires_at
        if expires_at.tzinfo is None:  # SQLite may return naive datetimes
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < now:
            raise ConflictError("Refresh token has expired.")
        row.consumed_at = now
        self._session.add(row)
        self._session.flush()
        return row.consultant_id

    @staticmethod
    def _to_prospect(row: ProspectORM) -> Prospect:
        return Prospect(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            company_name=row.company_name,
            stage=PipelineStage(row.stage),
            stage_entered_at=row.stage_entered_at,
            sector=row.sector,
            website=row.website,
            primary_contact_name=row.primary_contact_name,
            primary_contact_email=row.primary_contact_email,
            notes=row.notes,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_workshop(row: WorkshopORM) -> Workshop:
        return Workshop(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            prospect_id=row.prospect_id,
            state=WorkshopState(row.state),
            scheduled_for=row.scheduled_for,
            delivered_on=row.delivered_on,
            pre_workshop_brief=row.pre_workshop_brief,
            workshop_output=row.workshop_output,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_attribution(row: RecoveryFeeAttributionORM) -> RecoveryFeeAttribution:
        return RecoveryFeeAttribution(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            workshop_id=row.workshop_id,
            prospect_id=row.prospect_id,
            delivered_on=row.delivered_on,
            contracted_on=row.contracted_on,
            window_days=row.window_days,
            rate_ref=row.rate_ref,
            fee=Money(
                amount_minor=row.fee_amount_minor,
                currency=Currency(row.fee_currency),
                assumption_register_ref=row.fee_assumption_ref,
            ),
            content_hash=row.content_hash,
            created_at=row.created_at,
            # Append-only: the row is never updated, so updated mirrors created.
            updated_at=row.created_at,
        )

    def _to_engagement(self, row: EngagementORM) -> Engagement:
        assessment_ids = tuple(UUID(a) for a in json.loads(row.assessment_ids_json))
        deliverables = tuple(
            DeliverableSlot.model_validate(d) for d in json.loads(row.deliverables_json)
        )
        comms = tuple(self._to_comms_entry(c) for c in self._comms_for(row.id))
        return Engagement(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            prospect_id=row.prospect_id,
            title=row.title,
            status=EngagementStatus(row.status),
            started_on=row.started_on,
            assessment_ids=assessment_ids,
            deliverables=deliverables,
            comms_log=comms,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    @staticmethod
    def _to_comms_entry(row: CommsLogEntryORM) -> CommsLogEntry:
        return CommsLogEntry(
            id=row.id,
            at=row.at,
            channel=CommsChannel(row.channel),
            author_consultant_id=row.author_consultant_id,
            body=row.body,
        )

    # --- Shared client-report links + read tracking (GRS-0220) ----------------------------

    def _to_report_link(self, row: ClientReportLinkORM) -> ClientReportLink:
        return ClientReportLink(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            deliverable_id=row.deliverable_id,
            engagement_id=row.engagement_id,
            token_hash=row.token_hash,
            recipient_label=row.recipient_label,
            expires_at=row.expires_at,
            revoked_at=row.revoked_at,
            last_viewed_at=row.last_viewed_at,
        )

    def create_report_link(
        self,
        principal: Principal,
        *,
        deliverable_id: UUID,
        token_hash: str,
        recipient_label: str,
        report_json: str,
        expires_at: datetime,
    ) -> ClientReportLink:
        """Issue a link for one of the principal's OWN deliverables.

        The scope check is on the deliverable, not the link: issuing a link is the act of sharing
        that deliverable, so an advisor who cannot see it cannot share it either.
        """
        deliverable = self._require_deliverable(principal, deliverable_id)
        row = ClientReportLinkORM(
            owner_consultant_id=principal.consultant_id,
            deliverable_id=deliverable_id,
            engagement_id=deliverable.engagement_id,
            token_hash=token_hash,
            recipient_label=recipient_label,
            report_json=report_json,
            expires_at=expires_at,
        )
        self._session.add(row)
        self._session.flush()
        return self._to_report_link(row)

    def list_report_links(
        self, principal: Principal, deliverable_id: UUID
    ) -> list[ClientReportLink]:
        self._require_deliverable(principal, deliverable_id)  # scope check on the parent
        stmt = (
            select(ClientReportLinkORM)
            .where(ClientReportLinkORM.deliverable_id == deliverable_id)
            .where(ClientReportLinkORM.owner_consultant_id == principal.consultant_id)
            .order_by(ClientReportLinkORM.created_at.desc())
        )
        return [self._to_report_link(r) for r in self._session.execute(stmt).scalars().all()]

    def revoke_report_link(
        self, principal: Principal, link_id: UUID, *, at: datetime
    ) -> ClientReportLink:
        """Revoke immediately. Idempotent: re-revoking keeps the ORIGINAL timestamp, because when
        the advisor cut the client off is a fact about the first revocation, not the last click."""
        row = self._session.get(ClientReportLinkORM, link_id)
        if row is None:
            raise NotFoundError(f"Report link {link_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        if row.revoked_at is None:
            row.revoked_at = at
            self._session.flush()
        return self._to_report_link(row)

    def resolve_report_link_by_token_hash(self, token_hash: str) -> ClientReportLink | None:
        """Look a link up by token hash — the PUBLIC path, so it takes no principal.

        This is the one repository method with no scoping, and deliberately so: the token IS the
        credential, and the reader has no account to be scoped by. It returns the link whatever its
        state; the caller decides usability, so an expired and a revoked link are indistinguishable
        to anyone probing from outside.
        """
        stmt = select(ClientReportLinkORM).where(ClientReportLinkORM.token_hash == token_hash)
        row = self._session.execute(stmt).scalar_one_or_none()
        return self._to_report_link(row) if row is not None else None

    def report_snapshot_for_link(self, link_id: UUID) -> str:
        """The report JSON captured when the link was issued. Public path; no principal."""
        row = self._session.get(ClientReportLinkORM, link_id)
        if row is None:
            raise NotFoundError(f"Report link {link_id} not found.")
        return row.report_json

    def touch_report_link(self, link_id: UUID, *, at: datetime) -> None:
        """Record that the link was opened. Public path; no principal."""
        row = self._session.get(ClientReportLinkORM, link_id)
        if row is None:
            raise NotFoundError(f"Report link {link_id} not found.")
        row.last_viewed_at = at
        self._session.flush()

    def record_read_event(
        self, *, link_id: UUID, section: str, dwell_ms: int, occurred_at: datetime
    ) -> ReportReadEvent:
        """Append one read event. Public path; no principal — the token already authorised it."""
        row = ReportReadEventORM(
            link_id=link_id, section=section, dwell_ms=dwell_ms, occurred_at=occurred_at
        )
        self._session.add(row)
        self._session.flush()
        return ReportReadEvent(
            id=row.id,
            link_id=row.link_id,
            section=ReportSectionKind(row.section),
            dwell_ms=row.dwell_ms,
            occurred_at=row.occurred_at,
        )

    def read_summary_for_link(self, principal: Principal, link_id: UUID) -> ReportReadReport:
        """What the advisor sees: per-section views and total dwell for one of their own links."""
        link_row = self._session.get(ClientReportLinkORM, link_id)
        if link_row is None:
            raise NotFoundError(f"Report link {link_id} not found.")
        self._assert_can_access(principal, link_row.owner_consultant_id)

        stmt = select(ReportReadEventORM).where(ReportReadEventORM.link_id == link_id)
        events = list(self._session.execute(stmt).scalars().all())

        summaries: list[SectionReadSummary] = []
        for kind in SECTION_ORDER:
            for_section = [e for e in events if e.section == kind.value]
            moments = sorted(e.occurred_at for e in for_section)
            summaries.append(
                SectionReadSummary(
                    section=kind,
                    views=len(for_section),
                    total_dwell_ms=sum(e.dwell_ms for e in for_section),
                    first_viewed_at=moments[0] if moments else None,
                    last_viewed_at=moments[-1] if moments else None,
                )
            )
        link = self._to_report_link(link_row)
        return ReportReadReport(
            link_id=link.id,
            recipient_label=link.recipient_label,
            state=link.state(now=datetime.now(UTC)),
            sections=summaries,
        )

    # --- Client report prose (GRS-0211 wiring) ---------------------------------------------

    def get_report_prose(self, principal: Principal, deliverable_id: UUID) -> str | None:
        """The advisor's saved words for this deliverable's report, or None if unwritten."""
        self._require_deliverable(principal, deliverable_id)
        stmt = select(ClientReportProseORM).where(
            ClientReportProseORM.deliverable_id == deliverable_id
        )
        row = self._session.execute(stmt).scalar_one_or_none()
        return row.sections_json if row is not None else None

    def save_report_prose(
        self, principal: Principal, deliverable_id: UUID, *, sections_json: str
    ) -> None:
        """Upsert. A deliverable has one client report, so saving replaces rather than appends."""
        self._require_deliverable(principal, deliverable_id)
        stmt = select(ClientReportProseORM).where(
            ClientReportProseORM.deliverable_id == deliverable_id
        )
        row = self._session.execute(stmt).scalar_one_or_none()
        if row is None:
            row = ClientReportProseORM(
                owner_consultant_id=principal.consultant_id,
                deliverable_id=deliverable_id,
                sections_json=sections_json,
            )
            self._session.add(row)
        else:
            self._assert_can_access(principal, row.owner_consultant_id)
            row.sections_json = sections_json
        self._session.flush()
