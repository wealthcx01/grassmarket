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
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, Uuid
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
