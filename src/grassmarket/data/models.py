"""SQLAlchemy ORM models — the Grassmarket storage shapes.

These are storage records, distinct from the `bcap_contracts` wire/API shapes. The password
hash lives ONLY here (`ConsultantORM.hashed_password`) — never on a contract that could be
serialised to a client. Loop 0 persists exactly what the auth flow and the scoping tests need:
consultants, invitations, and one owned pipeline resource (prospects).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from bcap_contracts.common import AssessorLevel, ConsultantTier, Role
from bcap_contracts.entities import PipelineStage
from sqlalchemy import Boolean, DateTime, ForeignKey, String, Uuid
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
    sector: Mapped[str | None] = mapped_column(String(120), nullable=True)
    primary_contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    primary_contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
