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

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from bcap_contracts.auth import Consultant
from bcap_contracts.common import AssessorLevel, ConsultantTier, Role
from bcap_contracts.entities import PipelineStage, Prospect
from sqlalchemy import select
from sqlalchemy.orm import Session

from grassmarket.data.models import ConsultantORM, InvitationORM, ProspectORM


class RepositoryError(Exception):
    """Base class for repository failures. Never swallowed."""


class NotFoundError(RepositoryError):
    """A requested resource does not exist."""


class ScopeViolationError(RepositoryError):
    """A principal attempted to access a resource they do not own. The absolute-scoping guard."""


class ConflictError(RepositoryError):
    """A uniqueness/state conflict (e.g. duplicate email, already-accepted invitation)."""


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
        row = self._session.get(ProspectORM, prospect_id)
        if row is None:
            raise NotFoundError(f"Prospect {prospect_id} not found.")
        self._assert_can_access(principal, row.owner_consultant_id)
        row.stage = stage
        self._session.add(row)
        self._session.flush()
        return self._to_prospect(row)

    # ------------------------------------------------------------------ mappers
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
            sector=row.sector,
            primary_contact_name=row.primary_contact_name,
            primary_contact_email=row.primary_contact_email,
            notes=row.notes,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
