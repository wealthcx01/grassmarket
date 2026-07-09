"""engagements + comms_log_entries

GRS-0013: the engagement record tying a contracted prospect to its finalised assessment(s), a
deliverables progress shell (JSON, Loop 4 fills content), and an append-only communication log.

Revision ID: 0005_engagements
Revises: 0004_workshops_recovery_fees
Create Date: 2026-07-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_engagements"
down_revision = "0004_workshops_recovery_fees"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "engagements",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("prospect_id", sa.Uuid(), sa.ForeignKey("prospects.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_on", sa.Date(), nullable=True),
        sa.Column("assessment_ids_json", sa.Text(), nullable=False),
        sa.Column("deliverables_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_engagements_owner_consultant_id", "engagements", ["owner_consultant_id"], unique=False
    )
    op.create_index("ix_engagements_prospect_id", "engagements", ["prospect_id"], unique=False)

    op.create_table(
        "comms_log_entries",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("engagement_id", sa.Uuid(), sa.ForeignKey("engagements.id"), nullable=False),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("author_consultant_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_comms_log_entries_owner_consultant_id",
        "comms_log_entries",
        ["owner_consultant_id"],
        unique=False,
    )
    op.create_index(
        "ix_comms_log_entries_engagement_id",
        "comms_log_entries",
        ["engagement_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("comms_log_entries")
    op.drop_table("engagements")
