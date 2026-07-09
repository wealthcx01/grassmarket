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
from bcap_contracts.engagements import Workshop, WorkshopState
from bcap_contracts.entities import PipelineStage, Prospect
from bcap_contracts.fees import (
    RecoveryFeeAttribution,
    RecoveryFeeConfig,
    load_recovery_fee_config,
)
from bcap_contracts.money import Currency, Money
from bcap_contracts.pipeline import assert_legal_transition
from sqlalchemy import select
from sqlalchemy.orm import Session

from grassmarket.atlas import AssessmentInputs, AtlasResult
from grassmarket.data.models import (
    AssessmentORM,
    ConsultantORM,
    InvitationORM,
    ProspectORM,
    RecoveryFeeAttributionORM,
    ScoringRunORM,
    WorkshopORM,
)
from grassmarket.pipeline.fees import attribution_content_hash, is_within_attribution_window


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
