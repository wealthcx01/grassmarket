"""refresh_tokens

GRS-0120: a long-lived, single-use, rotated refresh token so an active advisor is not signed out at
the 30-minute access TTL. Only the hash is stored; consumed_at enforces single use, revoked_at
supports explicit logout.

Revision ID: 0023_refresh_tokens
Revises: 0022_c_benchmark_rows
Create Date: 2026-07-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0023_refresh_tokens"
down_revision = "0022_c_benchmark_rows"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index(
        "ix_refresh_tokens_consultant_id", "refresh_tokens", ["consultant_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_consultant_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
