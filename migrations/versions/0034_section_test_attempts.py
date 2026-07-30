"""section_test_attempts

GRS-0226 (GRS-0215's gate, finally wired): one row per attempt at one section's test.

Append-only. A retake is a NEW row rather than an update, so the record shows how many goes it took
instead of only the last answer — which is what makes the gate readable as evidence later. There is
deliberately no unique constraint on (advisor, module): retaking is the normal case, not a
conflict.

`score` is the fraction correct at the time of the attempt, stored rather than recomputed, because
the published course version it was marked against can be superseded.

Revision ID: 0034_section_test_attempts
Revises: 0033_founder_review
Create Date: 2026-07-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0034_section_test_attempts"
down_revision = "0033_founder_review"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "section_test_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_consultant_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        # The section (CourseModule) id inside the published tree. Not a foreign key: modules live
        # in the version's JSON snapshot, not in a table of their own.
        sa.Column("module_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        # `created_at` only, following `course_versions` rather than `courses`: this table is
        # append-only, and an `updated_at` column would advertise a mutation that never happens.
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_consultant_id"], ["consultants.id"]),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
    )
    # The reader's question is always "what has THIS advisor done on THIS course", so index the
    # pair rather than either column alone.
    op.create_index(
        "ix_section_test_attempts_owner_course",
        "section_test_attempts",
        ["owner_consultant_id", "course_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_section_test_attempts_owner_course", table_name="section_test_attempts")
    op.drop_table("section_test_attempts")
