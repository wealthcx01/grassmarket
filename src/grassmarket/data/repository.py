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
from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID

from bcap_contracts.assessments import (
    Assessment,
    AssessmentDocument,
    AssessmentState,
    ScoringRun,
)
from bcap_contracts.auth import Consultant
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
from bcap_contracts.money import Currency, Money
from bcap_contracts.narratives import AINarrative, NarrativeSection, NarrativeStatus
from bcap_contracts.pipeline import assert_legal_transition
from sqlalchemy import select
from sqlalchemy.orm import Session

from grassmarket.atlas import AssessmentInputs, AtlasResult
from grassmarket.data.models import (
    AINarrativeORM,
    AssessmentORM,
    CommsLogEntryORM,
    ConsultantORM,
    DeliverableORM,
    EngagementORM,
    InvitationORM,
    ProspectORM,
    RecoveryFeeAttributionORM,
    ScoringRunORM,
    WorkshopORM,
)
from grassmarket.pipeline.fees import attribution_content_hash, is_within_attribution_window

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
        without scoring. A FINALISED assessment refuses edits (its inputs are locked)."""
        row = self._require_assessment(principal, assessment_id)
        if row.state == AssessmentState.FINALISED.value:
            raise ConflictError(
                f"Assessment {assessment_id} is finalised; its inputs are locked (#6)."
            )
        row.document_json = document.model_dump_json()
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
