"""learning_drills

GRS-0024: the Workbench teaching half. Four tables: drill_cards (per-advisor SM-2 spaced-repetition
state, unique per (advisor, topic)); learning_modules (shared content); content_completions (an
advisor's completion, unique per (advisor, module), feeding certification evidence);
generated_quizzes
(AI-drafted, approval-gated). Scoped by owner_consultant_id.

Revision ID: 0012_learning_drills
Revises: 0011_certification
Create Date: 2026-07-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0012_learning_drills"
down_revision = "0011_certification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "drill_cards",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("topic", sa.String(length=128), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.Column("easiness", sa.Float(), nullable=False),
        sa.Column("interval_days", sa.Integer(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("streak", sa.Integer(), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_consultant_id", "topic", name="uq_drill_card_owner_topic"),
    )
    op.create_index(
        "ix_drill_cards_owner_consultant_id", "drill_cards", ["owner_consultant_id"], unique=False
    )
    op.create_table(
        "learning_modules",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("methodology_ref", sa.String(length=200), nullable=False),
        sa.Column("certification_credit", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_learning_modules_owner_consultant_id",
        "learning_modules",
        ["owner_consultant_id"],
        unique=False,
    )
    op.create_table(
        "content_completions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("module_id", sa.Uuid(), sa.ForeignKey("learning_modules.id"), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "owner_consultant_id", "module_id", name="uq_content_completion_owner_module"
        ),
    )
    op.create_index(
        "ix_content_completions_owner_consultant_id",
        "content_completions",
        ["owner_consultant_id"],
        unique=False,
    )
    op.create_table(
        "generated_quizzes",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("questions_json", sa.Text(), nullable=False),
        sa.Column("drafter_version", sa.String(length=64), nullable=False),
        sa.Column("approved_by_consultant_id", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_generated_quizzes_owner_consultant_id",
        "generated_quizzes",
        ["owner_consultant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("generated_quizzes")
    op.drop_table("content_completions")
    op.drop_table("learning_modules")
    op.drop_table("drill_cards")
