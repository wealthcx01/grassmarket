"""commission_v7_fields

GRS-0075 / ADR-0026: Commission Schedule v7 two-stream provenance on commission_lines. Adds
stream / product_id / delivery_type / contract_year / window_end (sealed in the content hash) and
client_paid_on (the pay-when-paid anchor GRS-0076 gates on). All nullable — existing v1 / recovery-
fee lines keep null provenance (non-retroactive).

Revision ID: 0021_commission_v7_fields
Revises: 0020_login_handoff_codes
Create Date: 2026-07-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0021_commission_v7_fields"
down_revision = "0020_login_handoff_codes"
branch_labels = None
depends_on = None

_COLUMNS = (
    ("stream", sa.String(length=16)),
    ("product_id", sa.String(length=64)),
    ("delivery_type", sa.String(length=24)),
    ("contract_year", sa.Integer()),
    ("window_end", sa.Date()),
    ("client_paid_on", sa.Date()),
)


def upgrade() -> None:
    for name, type_ in _COLUMNS:
        op.add_column("commission_lines", sa.Column(name, type_, nullable=True))


def downgrade() -> None:
    for name, _ in reversed(_COLUMNS):
        op.drop_column("commission_lines", name)
