"""course_cert_subject

GRS-0127 / ADR-0028: course & product certifications reuse the certification_events audit store —
add a nullable `cert_subject` (NULL = the assessor ladder; a value = a course/product cert). No
parallel cert store. Existing rows stay NULL (ladder events).

Revision ID: 0027_course_cert_subject
Revises: 0026_academy_courses
Create Date: 2026-07-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0027_course_cert_subject"
down_revision = "0026_academy_courses"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "certification_events",
        sa.Column("cert_subject", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("certification_events", "cert_subject")
