"""prospects.stage_entered_at

GRS-0011: the time-in-stage basis. Every prospect records when it entered its current stage; the
column backfills existing rows with the current timestamp (server default) and is not null.

Revision ID: 0003_prospect_stage_entered_at
Revises: 0002_assessments
Create Date: 2026-07-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_prospect_stage_entered_at"
down_revision = "0002_assessments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "prospects",
        sa.Column(
            "stage_entered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_column("prospects", "stage_entered_at")
