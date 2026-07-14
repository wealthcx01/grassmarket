"""extractions

GRS-0030: Path B extraction → review. Two tables: extractions (a gated proposal — the proposed
AssessmentDocument lives here, not on the assessment, until confirmed) and field_provenances (per
field: transcript span, confidence, accepted). Scoped by owner_consultant_id.

Revision ID: 0016_extractions
Revises: 0015_meeting_transcripts
Create Date: 2026-07-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0016_extractions"
down_revision = "0015_meeting_transcripts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "extractions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("assessment_id", sa.Uuid(), nullable=False),
        sa.Column("transcript_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("proposed_document_json", sa.Text(), nullable=False),
        sa.Column("gaps_json", sa.Text(), nullable=False),
        sa.Column("extractor_version", sa.String(length=64), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_extractions_owner_consultant_id", "extractions", ["owner_consultant_id"], unique=False
    )
    op.create_index("ix_extractions_assessment_id", "extractions", ["assessment_id"], unique=False)
    op.create_index("ix_extractions_transcript_id", "extractions", ["transcript_id"], unique=False)

    op.create_table(
        "field_provenances",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("extraction_id", sa.Uuid(), sa.ForeignKey("extractions.id"), nullable=False),
        sa.Column("transcript_id", sa.Uuid(), nullable=False),
        sa.Column("field_ref", sa.String(length=128), nullable=False),
        sa.Column("confidence", sa.String(length=8), nullable=False),
        sa.Column("span_start", sa.Integer(), nullable=False),
        sa.Column("span_end", sa.Integer(), nullable=False),
        sa.Column("accepted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_field_provenances_owner_consultant_id",
        "field_provenances",
        ["owner_consultant_id"],
        unique=False,
    )
    op.create_index(
        "ix_field_provenances_extraction_id",
        "field_provenances",
        ["extraction_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("field_provenances")
    op.drop_table("extractions")
