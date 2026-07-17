"""assessment_provenance

GRS-0119 / ADR-0029: record provenance on assessments — production (default) vs demo/sandbox.
A non-production record may self-approve/finalise (watermarked, non-promotable) without the
dual-rating + committee gate. Existing rows backfill to 'production'.

Revision ID: 0024_assessment_provenance
Revises: 0023_refresh_tokens
Create Date: 2026-07-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0024_assessment_provenance"
down_revision = "0023_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "assessments",
        sa.Column(
            "provenance",
            sa.String(length=16),
            nullable=False,
            server_default="production",
        ),
    )


def downgrade() -> None:
    op.drop_column("assessments", "provenance")
