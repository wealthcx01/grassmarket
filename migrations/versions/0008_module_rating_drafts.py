"""module_rating_drafts

GRS-0020: dual-rating + consensus (Methodology §9). One row per rater per module — a rater's
independent, blind rating of that module's subcomponents. The (assessment, module, rater) triple is
unique. Consensus is resolved from ≥2 submitted drafts into the assessment document, so no separate
consensus table is needed (dissent rides into the immutable scoring run via the document → inputs).
Scoped by owner_consultant_id (the rater).

Revision ID: 0008_module_rating_drafts
Revises: 0007_ai_narratives
Create Date: 2026-07-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0008_module_rating_drafts"
down_revision = "0007_ai_narratives"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "module_rating_drafts",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("assessment_id", sa.Uuid(), sa.ForeignKey("assessments.id"), nullable=False),
        sa.Column("module_key", sa.String(length=64), nullable=False),
        sa.Column("ratings_json", sa.Text(), nullable=False),
        sa.Column("submitted", sa.Boolean(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "assessment_id",
            "module_key",
            "owner_consultant_id",
            name="uq_module_rating_draft_assessment_module_rater",
        ),
    )
    op.create_index(
        "ix_module_rating_drafts_owner_consultant_id",
        "module_rating_drafts",
        ["owner_consultant_id"],
        unique=False,
    )
    op.create_index(
        "ix_module_rating_drafts_assessment_id",
        "module_rating_drafts",
        ["assessment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("module_rating_drafts")
