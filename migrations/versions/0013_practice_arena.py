"""practice_arena

GRS-0025: Practice Arena. Two tables: arena_scenarios (shared discovery scenarios — case brief,
client persona, scoring targets as JSON) and arena_sessions (one advisor's session — transcript,
deterministic score, AI-drafted feedback labelled #8). Scoped by owner_consultant_id.

Revision ID: 0013_practice_arena
Revises: 0012_learning_drills
Create Date: 2026-07-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0013_practice_arena"
down_revision = "0012_learning_drills"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "arena_scenarios",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("brief", sa.Text(), nullable=False),
        sa.Column("client_persona", sa.Text(), nullable=False),
        sa.Column("targets_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_arena_scenarios_owner_consultant_id",
        "arena_scenarios",
        ["owner_consultant_id"],
        unique=False,
    )
    op.create_table(
        "arena_sessions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("scenario_id", sa.Uuid(), sa.ForeignKey("arena_scenarios.id"), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("transcript_json", sa.Text(), nullable=False),
        sa.Column("score_json", sa.Text(), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("feedback_is_ai_drafted", sa.Boolean(), nullable=False),
        sa.Column("drafter_version", sa.String(length=64), nullable=True),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_arena_sessions_owner_consultant_id",
        "arena_sessions",
        ["owner_consultant_id"],
        unique=False,
    )
    op.create_index(
        "ix_arena_sessions_scenario_id", "arena_sessions", ["scenario_id"], unique=False
    )


def downgrade() -> None:
    op.drop_table("arena_sessions")
    op.drop_table("arena_scenarios")
