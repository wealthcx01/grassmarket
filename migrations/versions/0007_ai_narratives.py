"""ai_narratives

GRS-0017: AI first-draft narratives, human-gated. One row per AI-drafted deliverable section, bound
to a deliverable + finalised scoring run, carrying the proposal, its versioned attribution, and the
approval trail (approver, timestamp, final text, edit diff). Scoped by owner_consultant_id.

Revision ID: 0007_ai_narratives
Revises: 0006_deliverables
Create Date: 2026-07-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007_ai_narratives"
down_revision = "0006_deliverables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_narratives",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("deliverable_id", sa.Uuid(), sa.ForeignKey("deliverables.id"), nullable=False),
        sa.Column("scoring_run_id", sa.Uuid(), nullable=False),
        sa.Column("section", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("proposed_text", sa.Text(), nullable=False),
        sa.Column("drafter_version", sa.String(length=64), nullable=False),
        sa.Column("prompt_template_version", sa.String(length=64), nullable=False),
        sa.Column("author_tier", sa.String(length=32), nullable=False),
        sa.Column("final_text", sa.Text(), nullable=True),
        sa.Column("approved_by_consultant_id", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("edit_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_ai_narratives_owner_consultant_id",
        "ai_narratives",
        ["owner_consultant_id"],
        unique=False,
    )
    op.create_index(
        "ix_ai_narratives_deliverable_id", "ai_narratives", ["deliverable_id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("ai_narratives")
