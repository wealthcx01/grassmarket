"""google_oauth

GRS-0073 / ADR-0024: Google OAuth sign-in. Bind the Google account id (`google_sub`) on the
consultant, and make `hashed_password` nullable so an OAuth-only account (no password) is valid.
Email/password login is unchanged — password accounts keep their hash.

Revision ID: 0019_google_oauth
Revises: 0018_audit_events
Create Date: 2026-07-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0019_google_oauth"
down_revision = "0018_audit_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("consultants", sa.Column("google_sub", sa.String(length=255), nullable=True))
    op.create_index("ix_consultants_google_sub", "consultants", ["google_sub"], unique=True)
    # SQLite cannot ALTER a column to drop NOT NULL in place; use the batch (table-rebuild) path,
    # which is a no-op-shaped rebuild on Postgres too.
    with op.batch_alter_table("consultants") as batch:
        batch.alter_column("hashed_password", existing_type=sa.String(length=255), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("consultants") as batch:
        batch.alter_column("hashed_password", existing_type=sa.String(length=255), nullable=False)
    op.drop_index("ix_consultants_google_sub", table_name="consultants")
    op.drop_column("consultants", "google_sub")
