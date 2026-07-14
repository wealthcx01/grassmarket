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

import hashlib
import json
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
    ModuleRatingDraft,
    ScoringRun,
    SubcomponentRating,
)
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
)
from bcap_contracts.commissions import (
    CommissionKind,
    CommissionLine,
    EarningsSummary,
    PaymentStatus,
    SourcingAttribution,
    load_commission_config,
)
from bcap_contracts.committee import (
    CommitteeDecision,
    CommitteeDecisionStatus,
    CommitteeItemType,
)
from bcap_contracts.common import AssessorLevel, ConsultantTier, Role, UncertaintyRating
from bcap_contracts.deliverables import (
    ApprovalStatus,
    Deliverable,
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
from bcap_contracts.entities import PipelineStage, Prospect
from bcap_contracts.fees import (
    RecoveryFeeAttribution,
    RecoveryFeeConfig,
    load_recovery_fee_config,
)
from bcap_contracts.learning import (
    CertificationCredit,
    ContentCompletion,
    DrillCard,
    GeneratedQuiz,
    LearningKind,
    LearningModule,
    QuizQuestion,
    QuizStatus,
)
from bcap_contracts.money import Currency, Money
from bcap_contracts.narratives import AINarrative, NarrativeSection, NarrativeStatus
from bcap_contracts.pipeline import assert_legal_transition
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from grassmarket.atlas import AssessmentInputs, AtlasResult
from grassmarket.data.models import (
    AINarrativeORM,
    ArenaScenarioORM,
    ArenaSessionORM,
    AssessmentORM,
    CalibrationRatingORM,
    CalibrationSessionORM,
    CertificationEventORM,
    CertificationRecordORM,
    CommissionLineORM,
    CommitteeDecisionORM,
    CommsLogEntryORM,
    ConsultantORM,
    ContentCompletionORM,
    DeliverableORM,
    DrillCardORM,
    EngagementORM,
    GeneratedQuizORM,
    InvitationORM,
    LearningModuleORM,
    ModuleRatingDraftORM,
    ProspectORM,
    RecoveryFeeAttributionORM,
    ScoringRunORM,
    WorkshopORM,
)
from grassmarket.earnings.commission import (
    commission_content_hash,
    compute_engagement_commission,
)
from grassmarket.pipeline.fees import attribution_content_hash, is_within_attribution_window
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


class EngagementLinkError(RepositoryError):
    """An engagement was asked to link something it may not — a prospect that isn't contracted, or
    an assessment that isn't the owner's or isn't finalised. Fail loud rather than link loosely."""


@dataclass(frozen=True)
class Principal:
    """The authenticated identity every scoped call is made on behalf of. Produced by the auth
    layer from the JWT; consumed here to scope. `consultant_id` is the owner key."""

    consultant_id: UUID
    role: Role

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
    hashed_password: str
    role: Role
    tier: ConsultantTier
    assessor_level: AssessorLevel
    is_active: bool
    created_at: datetime
    updated_at: datetime

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

    def create_consultant(
        self,
        *,
        email: str,
        full_name: str,
        hashed_password: str,
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
        primary_contact_name: str | None = None,
        primary_contact_email: str | None = None,
        notes: str | None = None,
    ) -> Prospect:
        """Create a prospect owned by the principal. A consultant can only create for themselves —
        the owner is taken from the principal, never from caller-supplied input."""
        row = ProspectORM(
            owner_consultant_id=principal.consultant_id,
            company_name=company_name,
            stage=stage,
            sector=sector,
            primary_contact_name=primary_contact_name,
            primary_contact_email=primary_contact_email,
            notes=notes,
        )
        self._session.add(row)
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
        assert_legal_transition(PipelineStage(row.stage), stage)
        row.stage = stage
        row.stage_entered_at = datetime.now(UTC)
        self._session.add(row)
        self._session.flush()
        return self._to_prospect(row)

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
            content_hash=content_hash,
        )
        self._session.add(row)
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise ConflictError("This recovery fee has already been claimed.") from exc
        return self._to_commission_line(row)

    def record_engagement_commission(
        self,
        principal: Principal,
        *,
        advisor_id: UUID,
        engagement_id: UUID,
        base_value: Money,
        attribution: SourcingAttribution,
        earned_on: date,
    ) -> CommissionLine:
        """Record an engagement commission for an advisor — ADMIN only. The rate is the config rate
        for the advisor's tier × attribution AT RECORD TIME, stamped via rate_ref so a later config
        change is never retroactive. Immutable + content-hash-sealed."""
        if not principal.is_admin:
            raise ScopeViolationError("Only an admin may record a commission.")
        advisor = self._require_consultant(advisor_id)
        config = load_commission_config()
        tier = ConsultantTier(advisor.tier)
        amount = compute_engagement_commission(base_value, tier, attribution, config)
        return self._new_commission_line(
            owner_consultant_id=advisor_id,
            engagement_id=engagement_id,
            kind=CommissionKind.ENGAGEMENT,
            amount=amount,
            earned_on=earned_on,
            tier=tier,
            attribution=attribution,
            rate_ref=config.rate_ref(tier, attribution),
            base_value=base_value,
            source_attribution_id=None,
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
        row.payment_status = to_status.value
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
            content_hash=row.content_hash,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

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
        return self._to_deliverable(row)

    def get_deliverable(self, principal: Principal, deliverable_id: UUID) -> Deliverable:
        return self._to_deliverable(self._require_deliverable(principal, deliverable_id))

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
    def create_assessment(self, principal: Principal, *, subject: str = "") -> Assessment:
        """Create an empty draft assessment owned by the principal (owner never caller-supplied)."""
        row = AssessmentORM(
            owner_consultant_id=principal.consultant_id,
            subject=subject,
            state=AssessmentState.DRAFT.value,
            document_json=AssessmentDocument(subject=subject).model_dump_json(),
        )
        self._session.add(row)
        self._session.flush()
        return self._to_assessment(row)

    def get_assessment(self, principal: Principal, assessment_id: UUID) -> Assessment:
        return self._to_assessment(self._require_assessment(principal, assessment_id))

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
        self._session.flush()
        return self._to_assessment(row)

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
            state=AssessmentState(row.state),
            document=AssessmentDocument.model_validate_json(row.document_json),
            finalised_at=row.finalised_at,
            scoring_run_id=row.scoring_run_id,
            engine_version=row.engine_version,
            methodology_version=row.methodology_version,
            coefficient_version=row.coefficient_version,
            uncertainty_version=row.uncertainty_version,
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
    ) -> None:
        self._session.add(
            CertificationEventORM(
                owner_consultant_id=consultant_id,
                kind=kind.value,
                detail=detail,
                from_level=from_level.value if from_level else None,
                to_level=to_level.value if to_level else None,
                reason=reason,
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
            recorded_by_consultant_id=row.recorded_by_consultant_id,
            occurred_at=row.occurred_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

    # ------------------------------------------------- Power Drills (SCOPED, SM-2, GRS-0024)
    # Each advisor owns their own spaced-repetition cards; answering one reschedules it by SM-2. The
    # clock is injected (never `datetime.now()` inside), so the schedule is deterministic in tests.

    def create_drill_card(self, principal: Principal, *, topic: str, now: datetime) -> DrillCard:
        """Add a drill card for the caller over a topic — due immediately. One card per topic."""
        row = DrillCardORM(
            owner_consultant_id=principal.consultant_id,
            topic=topic,
            due_at=now,
        )
        self._session.add(row)
        try:
            self._session.flush()
        except IntegrityError as exc:
            self._session.rollback()
            raise ConflictError(f"You already have a drill card for {topic!r}.") from exc
        return self._to_drill_card(row)

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
    def _to_drill_card(row: DrillCardORM) -> DrillCard:
        return DrillCard(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            topic=row.topic,
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

        items = assemble_queue(
            cert_record=cert_record,
            next_coursework=next_coursework,
            due_drills=due_drills,
            arena_scenario=arena_scenario,
            research_prospect=research_prospect,
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
        )

    @staticmethod
    def _to_prospect(row: ProspectORM) -> Prospect:
        return Prospect(
            id=row.id,
            owner_consultant_id=row.owner_consultant_id,
            company_name=row.company_name,
            stage=PipelineStage(row.stage),
            stage_entered_at=row.stage_entered_at,
            sector=row.sector,
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
