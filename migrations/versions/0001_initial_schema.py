"""initial schema — consultants, invitations, prospects, scoring_runs

The first migration (GRS-0006): it is the schema source of truth, replacing `create_all` on the app
path. It captures the tables shipped through Loop 0/1 — identity + one pipeline resource — plus the
immutable, content-hashed `scoring_runs` table this ticket introduces.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "consultants",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("tier", sa.String(length=32), nullable=False),
        sa.Column("assessor_level", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_consultants_email", "consultants", ["email"], unique=True)

    op.create_table(
        "invitations",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("tier", sa.String(length=32), nullable=False),
        sa.Column("invited_by_consultant_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_invitations_email", "invitations", ["email"], unique=False)
    op.create_index("ix_invitations_token_hash", "invitations", ["token_hash"], unique=True)

    op.create_table(
        "prospects",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id",
            sa.Uuid(),
            sa.ForeignKey("consultants.id"),
            nullable=False,
        ),
        sa.Column("company_name", sa.String(length=200), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("sector", sa.String(length=120), nullable=True),
        sa.Column("primary_contact_name", sa.String(length=200), nullable=True),
        sa.Column("primary_contact_email", sa.String(length=320), nullable=True),
        sa.Column("notes", sa.String(length=2000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_prospects_owner_consultant_id", "prospects", ["owner_consultant_id"], unique=False
    )

    op.create_table(
        "scoring_runs",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id",
            sa.Uuid(),
            sa.ForeignKey("consultants.id"),
            nullable=False,
        ),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("engine_version", sa.String(length=64), nullable=False),
        sa.Column("methodology_version", sa.String(length=64), nullable=False),
        sa.Column("coefficient_version", sa.String(length=128), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("inputs_json", sa.Text(), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=False),
        sa.Column("v_index", sa.Float(), nullable=True),
        sa.Column("v_p10", sa.Float(), nullable=True),
        sa.Column("v_p90", sa.Float(), nullable=True),
        sa.Column("uncertainty_rating", sa.String(length=16), nullable=True),
        sa.Column("finalised", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_scoring_runs_owner_consultant_id", "scoring_runs", ["owner_consultant_id"], unique=False
    )
    op.create_index(
        "ix_scoring_runs_assessment_id", "scoring_runs", ["assessment_id"], unique=False
    )
    op.create_index("ix_scoring_runs_content_hash", "scoring_runs", ["content_hash"], unique=False)


def downgrade() -> None:
    op.drop_table("scoring_runs")
    op.drop_table("prospects")
    op.drop_table("invitations")
    op.drop_table("consultants")
