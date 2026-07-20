"""contacts_and_prospect_website

GRS-0111 (CRM rebuild): first-class Contact entity (many per prospect, owner-scoped) + a `website`
column on prospects. Existing prospects keep their inline primary_contact_* fields; the Contact
table adds the whole buying unit.

Revision ID: 0029_contacts_and_prospect_website
Revises: 0028_cert_event_assessment_id
Create Date: 2026-07-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0029_contacts_and_prospect_website"
down_revision = "0028_cert_event_assessment_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Widen alembic_version.version_num before recording this revision. Alembic's default is
    # varchar(32), but this revision id is 34 chars — on Postgres the version UPDATE at the end of
    # this migration raises StringDataRightTruncation and the deploy's boot migration fails. (SQLite,
    # used by local/CI, ignores column length, so it only bites production.) Widen once, Postgres-
    # only, so this and any future longer revision ids record cleanly; this runs in the same
    # transaction as the version UPDATE, which then fits.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)")

    op.add_column("prospects", sa.Column("website", sa.String(length=255), nullable=True))
    op.create_table(
        "contacts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "owner_consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False
        ),
        sa.Column("prospect_id", sa.Uuid(), sa.ForeignKey("prospects.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("phone", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=160), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_contacts_owner_consultant_id", "contacts", ["owner_consultant_id"])
    op.create_index("ix_contacts_prospect_id", "contacts", ["prospect_id"])


def downgrade() -> None:
    op.drop_table("contacts")
    op.drop_column("prospects", "website")
