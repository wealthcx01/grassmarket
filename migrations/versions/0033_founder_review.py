"""founder_review

GRS-0188 (ADR-0041): the founder review gate. `founder_approvals` is an append-only record of the
founder signing off one version of one assessment document, identified by the sha256 of that
document. Nothing is ever updated or deleted here; an edit produces a new hash, the old approval
stops matching, and the record is back in the queue.

`assessments.review_requested_at` is the advisor's side of the same handshake: when they asked for
review. Nullable, because most records have never been submitted.

Revision ID: 0033_founder_review
Revises: 0032_gtm_registry
Create Date: 2026-07-29
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0033_founder_review"
down_revision = "0032_gtm_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "founder_approvals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        # The advisor who owns the assessment, not the founder. Scoping stays theirs.
        sa.Column("owner_consultant_id", sa.Uuid(), nullable=False),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("document_hash", sa.String(length=64), nullable=False),
        sa.Column("approved_by_consultant_id", sa.Uuid(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"]),
        sa.ForeignKeyConstraint(["owner_consultant_id"], ["consultants.id"]),
        sa.ForeignKeyConstraint(["approved_by_consultant_id"], ["consultants.id"]),
    )
    op.create_index(
        "ix_founder_approvals_assessment_id", "founder_approvals", ["assessment_id"]
    )
    op.add_column(
        "assessments",
        sa.Column("review_requested_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("assessments", "review_requested_at")
    op.drop_index("ix_founder_approvals_assessment_id", table_name="founder_approvals")
    op.drop_table("founder_approvals")
