"""calibration

GRS-0022: calibration module (Methodology §9). Two tables: calibration_sessions (a facilitator's
round of shared vignettes; the computed per-anchor result is stamped into results_json on close) and
calibration_ratings (one assessor's blind rating set, unique per (session, assessor), contributing
to the result only when submitted). Scoped by owner_consultant_id (facilitator / assessor).

Revision ID: 0010_calibration
Revises: 0009_committee_decisions
Create Date: 2026-07-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0010_calibration"
down_revision = "0009_committee_decisions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "calibration_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("vignettes_json", sa.Text(), nullable=False),
        sa.Column("results_json", sa.Text(), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_calibration_sessions_owner_consultant_id",
        "calibration_sessions",
        ["owner_consultant_id"],
        unique=False,
    )
    op.create_table(
        "calibration_ratings",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column(
            "session_id", sa.Uuid(), sa.ForeignKey("calibration_sessions.id"), nullable=False
        ),
        sa.Column("entries_json", sa.Text(), nullable=False),
        sa.Column("submitted", sa.Boolean(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "session_id", "owner_consultant_id", name="uq_calibration_rating_session_rater"
        ),
    )
    op.create_index(
        "ix_calibration_ratings_owner_consultant_id",
        "calibration_ratings",
        ["owner_consultant_id"],
        unique=False,
    )
    op.create_index(
        "ix_calibration_ratings_session_id", "calibration_ratings", ["session_id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("calibration_ratings")
    op.drop_table("calibration_sessions")
