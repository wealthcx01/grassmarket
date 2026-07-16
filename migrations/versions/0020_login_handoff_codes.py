"""login_handoff_codes

GRS-0074 / ADR-0024: single-use, short-TTL codes for the cross-site login hand-off. The OAuth
callback issues one bound to the verified consultant; the advisory app exchanges it (server-side)
for the GM JWT — the JWT never rides in a URL. Only the hash is stored; `consumed_at` makes it
single-use.

Revision ID: 0020_login_handoff_codes
Revises: 0019_google_oauth
Create Date: 2026-07-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0020_login_handoff_codes"
down_revision = "0019_google_oauth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "login_handoff_codes",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("consultant_id", sa.Uuid(), sa.ForeignKey("consultants.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_login_handoff_codes_code_hash", "login_handoff_codes", ["code_hash"], unique=True
    )
    op.create_index(
        "ix_login_handoff_codes_consultant_id", "login_handoff_codes", ["consultant_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_login_handoff_codes_consultant_id", table_name="login_handoff_codes")
    op.drop_index("ix_login_handoff_codes_code_hash", table_name="login_handoff_codes")
    op.drop_table("login_handoff_codes")
