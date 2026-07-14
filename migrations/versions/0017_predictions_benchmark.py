"""predictions_benchmark

GRS-0031: prediction register + anonymised benchmark. Two tables: predictions (lever-level, scored
on follow-up, owner-scoped) and benchmark_rows (ANONYMISED finalised scores — no client identity,
no owner, no run/assessment link).

Revision ID: 0017_predictions_benchmark
Revises: 0016_extractions
Create Date: 2026-07-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0017_predictions_benchmark"
down_revision = "0016_extractions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "predictions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("scoring_run_id", sa.Uuid(), nullable=False),
        sa.Column("lever", sa.String(length=32), nullable=False),
        sa.Column("predicted_delta_minor", sa.Integer(), nullable=False),
        sa.Column("predicted_delta_currency", sa.String(length=3), nullable=False),
        sa.Column("predicted_delta_ref", sa.String(length=160), nullable=False),
        sa.Column("horizon_months", sa.Integer(), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("follow_up_due", sa.Date(), nullable=False),
        sa.Column("outcome", sa.String(length=16), nullable=False),
        sa.Column("realised_delta_minor", sa.Integer(), nullable=True),
        sa.Column("realised_delta_currency", sa.String(length=3), nullable=True),
        sa.Column("realised_delta_ref", sa.String(length=160), nullable=True),
        sa.Column("brier_score", sa.Float(), nullable=True),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_predictions_owner_consultant_id", "predictions", ["owner_consultant_id"], unique=False
    )
    op.create_index(
        "ix_predictions_scoring_run_id", "predictions", ["scoring_run_id"], unique=False
    )
    op.create_index("ix_predictions_follow_up_due", "predictions", ["follow_up_due"], unique=False)

    op.create_table(
        "benchmark_rows",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("v_index", sa.Float(), nullable=False),
        sa.Column("v_p10", sa.Float(), nullable=True),
        sa.Column("v_p90", sa.Float(), nullable=True),
        sa.Column("uncertainty_rating", sa.String(length=16), nullable=True),
        sa.Column("methodology_version", sa.String(length=64), nullable=False),
        sa.Column("coefficient_version", sa.String(length=64), nullable=False),
        sa.Column("sector", sa.String(length=64), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("benchmark_rows")
    op.drop_table("predictions")
