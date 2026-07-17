"""prospect_stage_history

GRS-0111 / ADR-0027: append-only audit of prospect stage transitions — the timeline behind the
CRM board. One row per validated move (written at the update_prospect_stage choke-point) plus a
creation row (from_stage NULL). Owner-scoped like every pipeline resource.

Revision ID: 0025_prospect_stage_history
Revises: 0024_assessment_provenance
Create Date: 2026-07-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0025_prospect_stage_history"
down_revision = "0024_assessment_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prospect_stage_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "owner_consultant_id",
            sa.Uuid(),
            sa.ForeignKey("consultants.id"),
            nullable=False,
        ),
        sa.Column(
            "prospect_id",
            sa.Uuid(),
            sa.ForeignKey("prospects.id"),
            nullable=False,
        ),
        sa.Column("from_stage", sa.String(length=32), nullable=True),
        sa.Column("to_stage", sa.String(length=32), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_prospect_stage_history_owner_consultant_id",
        "prospect_stage_history",
        ["owner_consultant_id"],
    )
    op.create_index(
        "ix_prospect_stage_history_prospect_id",
        "prospect_stage_history",
        ["prospect_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_prospect_stage_history_prospect_id", table_name="prospect_stage_history")
    op.drop_index(
        "ix_prospect_stage_history_owner_consultant_id", table_name="prospect_stage_history"
    )
    op.drop_table("prospect_stage_history")
