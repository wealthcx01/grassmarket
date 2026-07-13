"""certification

GRS-0023: certification ladder (Methodology §9). Two tables: certification_records (one per advisor,
the accumulated ladder evidence — coursework/exam/shadow/observed-lead/sign-off) and
certification_events (append-only audit of every credit, promotion, and admin override). The
advisor's LEVEL stays on consultants.assessor_level (the JWT claim); these hold the evidence and the
audit trail. Scoped by owner_consultant_id (the advisor).

Revision ID: 0011_certification
Revises: 0010_calibration
Create Date: 2026-07-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0011_certification"
down_revision = "0010_calibration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "certification_records",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("coursework_complete", sa.Boolean(), nullable=False),
        sa.Column("exam_score", sa.Float(), nullable=True),
        sa.Column("shadow_count", sa.Integer(), nullable=False),
        sa.Column("observed_lead_logged", sa.Boolean(), nullable=False),
        sa.Column("observed_lead_signoff_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_consultant_id", name="uq_certification_record_consultant"),
    )
    op.create_index(
        "ix_certification_records_owner_consultant_id",
        "certification_records",
        ["owner_consultant_id"],
        unique=False,
    )
    op.create_table(
        "certification_events",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("from_level", sa.String(length=32), nullable=True),
        sa.Column("to_level", sa.String(length=32), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("recorded_by_consultant_id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_certification_events_owner_consultant_id",
        "certification_events",
        ["owner_consultant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("certification_events")
    op.drop_table("certification_records")
