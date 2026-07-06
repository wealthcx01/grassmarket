"""assessments table + scoring_runs.uncertainty_version

GRS-0009: the lifecycle-managed assessment (the intermediate document the wizard drives) and the
uncertainty-model version stamp on a scoring run's band (ADR-0008).

Revision ID: 0002_assessments
Revises: 0001_initial_schema
Create Date: 2026-07-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_assessments"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scoring_runs",
        sa.Column("uncertainty_version", sa.String(length=128), nullable=True),
    )

    op.create_table(
        "assessments",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id",
            sa.Uuid(),
            sa.ForeignKey("consultants.id"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("document_json", sa.Text(), nullable=False),
        sa.Column("finalised_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scoring_run_id", sa.Uuid(), nullable=True),
        sa.Column("engine_version", sa.String(length=64), nullable=True),
        sa.Column("methodology_version", sa.String(length=64), nullable=True),
        sa.Column("coefficient_version", sa.String(length=128), nullable=True),
        sa.Column("uncertainty_version", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_assessments_owner_consultant_id", "assessments", ["owner_consultant_id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("assessments")
    op.drop_column("scoring_runs", "uncertainty_version")
