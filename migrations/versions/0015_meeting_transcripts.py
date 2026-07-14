"""meeting_transcripts

GRS-0029: Path B ingestion. One table, meeting_transcripts — a pasted or transcribed meeting
transcript, stored ONLY as ciphertext (encrypted at rest), scoped by owner_consultant_id, with a
retention date for the GDPR groundwork.

Revision ID: 0015_meeting_transcripts
Revises: 0014_commission_lines
Create Date: 2026-07-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0015_meeting_transcripts"
down_revision = "0014_commission_lines"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meeting_transcripts",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("engagement_id", sa.Uuid(), nullable=True),
        sa.Column("source_kind", sa.String(length=24), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("text_ciphertext", sa.LargeBinary(), nullable=False),
        sa.Column("transcriber_ref", sa.String(length=64), nullable=False),
        sa.Column("retention_until", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_meeting_transcripts_owner_consultant_id",
        "meeting_transcripts",
        ["owner_consultant_id"],
        unique=False,
    )
    op.create_index(
        "ix_meeting_transcripts_engagement_id",
        "meeting_transcripts",
        ["engagement_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("meeting_transcripts")
