"""c_benchmark_rows

GRS-0084: the C (Customer-Proposition) benchmark set — NAMED public-app peers (Saxo, IBKR, …) with
their C-index + per-C-module scores, APPROVAL-GATED (ADR-0009): a row is not live until a consultant
records sign-off. A shared org-wide reference set (peers are public apps, not client data).

Revision ID: 0022_c_benchmark_rows
Revises: 0021_commission_v7_fields
Create Date: 2026-07-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0022_c_benchmark_rows"
down_revision = "0021_commission_v7_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "c_benchmark_rows",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("peer_name", sa.String(length=120), nullable=False),
        sa.Column("profile_key", sa.String(length=64), nullable=False),
        sa.Column("c_index", sa.Float(), nullable=False),
        sa.Column("module_scores", sa.JSON(), nullable=False),
        sa.Column("methodology_version", sa.String(length=64), nullable=False),
        sa.Column("coefficient_version", sa.String(length=64), nullable=False),
        sa.Column("source_ref", sa.String(length=160), nullable=True),
        sa.Column("approved", sa.Boolean(), nullable=False),
        sa.Column("approved_by", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_c_benchmark_rows_profile_key", "c_benchmark_rows", ["profile_key"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_c_benchmark_rows_profile_key", table_name="c_benchmark_rows")
    op.drop_table("c_benchmark_rows")
