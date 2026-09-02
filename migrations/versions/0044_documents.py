"""Documents an advisor uploads (GRS-0247).

The product had no general upload path: the only inbound route was POST /transcripts/media, which
takes audio or video, keeps the transcript and discards the file. A client's board pack had nowhere
to live.

Parented by prospect, workshop OR engagement — at least one — because a workshop is recorded while
the client is still a prospect (Backend Requests R2, 2026-09-02). Requiring engagement_id would
exclude the case the feature exists for.

Revision ID: 0044_documents
Revises: 0043_engagement_assessments
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0044_documents"
down_revision = "0043_engagement_assessments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column(
            "prospect_id",
            sa.Uuid(),
            sa.ForeignKey("prospects.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "workshop_id",
            sa.Uuid(),
            sa.ForeignKey("workshops.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "engagement_id",
            sa.Uuid(),
            sa.ForeignKey("engagements.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("content_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("provenance", sa.String(length=16), nullable=False, server_default="production"),
        sa.Column("scanner_ref", sa.String(length=64), nullable=False),
        sa.Column(
            "uploaded_by_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("retention_until", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "prospect_id IS NOT NULL OR workshop_id IS NOT NULL OR engagement_id IS NOT NULL",
            name="ck_documents_has_a_parent",
        ),
    )
    for column in ("owner_consultant_id", "prospect_id", "workshop_id", "engagement_id", "sha256"):
        op.create_index(f"ix_documents_{column}", "documents", [column])


def downgrade() -> None:
    for column in ("owner_consultant_id", "prospect_id", "workshop_id", "engagement_id", "sha256"):
        op.drop_index(f"ix_documents_{column}", table_name="documents")
    op.drop_table("documents")
