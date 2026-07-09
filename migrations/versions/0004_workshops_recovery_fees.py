"""workshops + recovery_fee_attributions

GRS-0012: workshop management (scheduled → delivered, linked to a prospect) and the append-only,
content-hashed Workshop Recovery Fee attribution (Money persisted as minor units + currency + the
assumption ref that justifies it).

Revision ID: 0004_workshops_recovery_fees
Revises: 0003_prospect_stage_entered_at
Create Date: 2026-07-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_workshops_recovery_fees"
down_revision = "0003_prospect_stage_entered_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workshops",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("prospect_id", sa.Uuid(), sa.ForeignKey("prospects.id"), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("scheduled_for", sa.Date(), nullable=True),
        sa.Column("delivered_on", sa.Date(), nullable=True),
        sa.Column("pre_workshop_brief", sa.Text(), nullable=True),
        sa.Column("workshop_output", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_workshops_owner_consultant_id", "workshops", ["owner_consultant_id"], unique=False
    )
    op.create_index("ix_workshops_prospect_id", "workshops", ["prospect_id"], unique=False)

    op.create_table(
        "recovery_fee_attributions",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column(
            "workshop_id", sa.Uuid(), sa.ForeignKey("workshops.id"), nullable=False, unique=True
        ),
        sa.Column("prospect_id", sa.Uuid(), nullable=False),
        sa.Column("delivered_on", sa.Date(), nullable=False),
        sa.Column("contracted_on", sa.Date(), nullable=False),
        sa.Column("window_days", sa.Integer(), nullable=False),
        sa.Column("rate_ref", sa.String(length=128), nullable=False),
        sa.Column("fee_amount_minor", sa.Integer(), nullable=False),
        sa.Column("fee_currency", sa.String(length=3), nullable=False),
        sa.Column("fee_assumption_ref", sa.String(length=128), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_recovery_fee_attributions_owner_consultant_id",
        "recovery_fee_attributions",
        ["owner_consultant_id"],
        unique=False,
    )
    op.create_index(
        "ix_recovery_fee_attributions_workshop_id",
        "recovery_fee_attributions",
        ["workshop_id"],
        unique=True,
    )
    op.create_index(
        "ix_recovery_fee_attributions_prospect_id",
        "recovery_fee_attributions",
        ["prospect_id"],
        unique=False,
    )
    op.create_index(
        "ix_recovery_fee_attributions_content_hash",
        "recovery_fee_attributions",
        ["content_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("recovery_fee_attributions")
    op.drop_table("workshops")
