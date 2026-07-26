"""gtm_registry

GRS-0193 (ADR-0045): the shared GTM target & contact registry. `registry_targets` is the imported
institution universe behind the existing `EntityRegistry` port; `registry_contacts` are the named
people at those institutions. Both are network-shared reference data with no owner column — the
one deliberate exception to owner-scoping, enforced and tested in the repository layer.

Revision ID: 0032_gtm_registry
Revises: 0031_drill_card_prompt_answer
Create Date: 2026-07-25
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0032_gtm_registry"
down_revision = "0031_drill_card_prompt_answer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "registry_targets",
        sa.Column("target_id", sa.String(length=160), primary_key=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("segment", sa.String(length=120), nullable=True),
        sa.Column("country", sa.String(length=120), nullable=True),
        sa.Column("ric", sa.String(length=32), nullable=True),
        sa.Column("ctb_id", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("imported_on", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_registry_targets_name", "registry_targets", ["name"])
    op.create_index("ix_registry_targets_ctb_id", "registry_targets", ["ctb_id"])

    op.create_table(
        "registry_contacts",
        sa.Column("contact_id", sa.String(length=200), primary_key=True),
        sa.Column(
            "target_id",
            sa.String(length=160),
            sa.ForeignKey("registry_targets.target_id"),
            nullable=False,
        ),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("job_role", sa.String(length=200), nullable=True),
        sa.Column("linkedin", sa.String(length=500), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("imported_on", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_registry_contacts_target_id", "registry_contacts", ["target_id"])
    op.create_index("ix_registry_contacts_email", "registry_contacts", ["email"])


def downgrade() -> None:
    op.drop_table("registry_contacts")
    op.drop_table("registry_targets")
