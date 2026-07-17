"""cert_event_assessment_id

GRS-0131 / ADR-0028: tie certification evidence to real assessment participation. A nullable
`assessment_id` on certification_events records the assessment a shadow / observed-lead credit was
auto-derived from, making the derivation idempotent per (advisor, assessment). Existing rows stay
NULL (admin-recorded, not derived).

Revision ID: 0028_cert_event_assessment_id
Revises: 0027_course_cert_subject
Create Date: 2026-07-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0028_cert_event_assessment_id"
down_revision = "0027_course_cert_subject"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "certification_events",
        sa.Column("assessment_id", sa.Uuid(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("certification_events", "assessment_id")
