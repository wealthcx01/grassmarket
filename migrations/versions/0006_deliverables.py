"""deliverables

GRS-0015: generated deliverable documents tied to an engagement. Metadata only — the .docx is
regenerated deterministically from the finalised scoring run on download. `mode` records the
client-usable gate's decision; the approval fields carry non-negotiable #8.

Revision ID: 0006_deliverables
Revises: 0005_engagements
Create Date: 2026-07-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_deliverables"
down_revision = "0005_engagements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deliverables",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("engagement_id", sa.Uuid(), sa.ForeignKey("engagements.id"), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("ai_generated", sa.Boolean(), nullable=False),
        sa.Column("approval_status", sa.String(length=20), nullable=False),
        sa.Column("approved_by_consultant_id", sa.Uuid(), nullable=True),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("scoring_run_id", sa.Uuid(), nullable=True),
        sa.Column("coefficient_version", sa.String(length=128), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_deliverables_owner_consultant_id", "deliverables", ["owner_consultant_id"], unique=False
    )
    op.create_index(
        "ix_deliverables_engagement_id", "deliverables", ["engagement_id"], unique=False
    )
    op.create_index("ix_deliverables_content_hash", "deliverables", ["content_hash"], unique=False)


def downgrade() -> None:
    op.drop_table("deliverables")
