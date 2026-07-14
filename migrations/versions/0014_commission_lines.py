"""commission_lines

GRS-0028: My Earnings. One table, commission_lines — an earned commission (engagement, workshop
recovery fee, or retainer), content-hash-sealed and immutable except its payment_status lifecycle
(pending → invoiced → paid). Money is stored as integer minor units + currency + assumption ref.
Scoped by owner_consultant_id.

Revision ID: 0014_commission_lines
Revises: 0013_practice_arena
Create Date: 2026-07-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0014_commission_lines"
down_revision = "0013_practice_arena"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commission_lines",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("engagement_id", sa.Uuid(), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("amount_currency", sa.String(length=3), nullable=False),
        sa.Column("amount_assumption_ref", sa.String(length=160), nullable=False),
        sa.Column("payment_status", sa.String(length=16), nullable=False),
        sa.Column("earned_on", sa.Date(), nullable=True),
        sa.Column("tier", sa.String(length=24), nullable=True),
        sa.Column("attribution", sa.String(length=24), nullable=True),
        sa.Column("rate_ref", sa.String(length=160), nullable=True),
        sa.Column("base_value_minor", sa.Integer(), nullable=True),
        sa.Column("base_value_currency", sa.String(length=3), nullable=True),
        sa.Column("base_value_ref", sa.String(length=160), nullable=True),
        sa.Column("source_attribution_id", sa.Uuid(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_commission_lines_owner_consultant_id",
        "commission_lines",
        ["owner_consultant_id"],
        unique=False,
    )
    op.create_index(
        "ix_commission_lines_engagement_id", "commission_lines", ["engagement_id"], unique=False
    )
    # One commission line per recovery-fee attribution — no double-claiming the same fee.
    op.create_index(
        "ix_commission_lines_source_attribution_id",
        "commission_lines",
        ["source_attribution_id"],
        unique=True,
    )
    op.create_index(
        "ix_commission_lines_content_hash", "commission_lines", ["content_hash"], unique=False
    )


def downgrade() -> None:
    op.drop_table("commission_lines")
