"""academy_courses

GRS-0121 / ADR-0028: the Bruntsfield Academy content model — courses (editable draft tree),
immutable published version snapshots (append-only), and per-lesson completions. Shared catalog
content; authoring is admin-gated in the repository layer.

Revision ID: 0026_academy_courses
Revises: 0025_prospect_stage_history
Create Date: 2026-07-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0026_academy_courses"
down_revision = "0025_prospect_stage_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("draft_json", sa.Text(), nullable=False),
        sa.Column("latest_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_courses_owner_consultant_id", "courses", ["owner_consultant_id"])
    op.create_index("ix_courses_slug", "courses", ["slug"], unique=True)

    op.create_table(
        "course_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("course_id", sa.Uuid(), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("tree_json", sa.Text(), nullable=False),
        sa.Column("published_by_consultant_id", sa.Uuid(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("course_id", "version", name="uq_course_version"),
    )
    op.create_index("ix_course_versions_course_id", "course_versions", ["course_id"])
    op.create_index("ix_course_versions_slug", "course_versions", ["slug"])

    op.create_table(
        "lesson_completions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("course_id", sa.Uuid(), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("lesson_id", sa.Uuid(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("owner_consultant_id", "lesson_id", name="uq_lesson_completion"),
    )
    op.create_index(
        "ix_lesson_completions_owner_consultant_id",
        "lesson_completions",
        ["owner_consultant_id"],
    )
    op.create_index("ix_lesson_completions_course_id", "lesson_completions", ["course_id"])


def downgrade() -> None:
    op.drop_table("lesson_completions")
    op.drop_table("course_versions")
    op.drop_table("courses")
