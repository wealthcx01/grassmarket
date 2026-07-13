"""committee_decisions

GRS-0021: Rating Committee queue (Methodology §8). One row per (assessment, item_type, item_key) —
the committee's call on a high-stakes rating (power Established+, triad above None, module
Frontier), at the rating it reviewed, with rationale and dissent. Scoped by owner_consultant_id (the
assessment owner); decided_by_consultant_id is the committee member (never the owner).

Revision ID: 0009_committee_decisions
Revises: 0008_module_rating_drafts
Create Date: 2026-07-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_committee_decisions"
down_revision = "0008_module_rating_drafts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "committee_decisions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("assessment_id", sa.Uuid(), sa.ForeignKey("assessments.id"), nullable=False),
        sa.Column("item_type", sa.String(length=16), nullable=False),
        sa.Column("item_key", sa.String(length=64), nullable=False),
        sa.Column("rating", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("dissent_note", sa.Text(), nullable=True),
        sa.Column("decided_by_consultant_id", sa.Uuid(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "assessment_id", "item_type", "item_key", name="uq_committee_decision_assessment_item"
        ),
    )
    op.create_index(
        "ix_committee_decisions_owner_consultant_id",
        "committee_decisions",
        ["owner_consultant_id"],
        unique=False,
    )
    op.create_index(
        "ix_committee_decisions_assessment_id",
        "committee_decisions",
        ["assessment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("committee_decisions")
