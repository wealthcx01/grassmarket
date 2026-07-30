"""client_report_prose

GRS-0219/0220 wiring: somewhere for the advisor's words to live.

The client report's content model (GRS-0211) takes prose as an INPUT and refuses to build without
it, deliberately — "what this firm is and how it makes money" is not derivable from a scoring run,
and inventing it would be the silent fabrication non-negotiable #3 forbids. Until now nothing
stored that prose, so nothing could actually render a report. This table is that gap closed.

One row per deliverable, all six sections in one JSON column: they are written, reviewed and saved
as a single document, so splitting them into rows would buy nothing but joins.

Revision ID: 0036_client_report_prose
Revises: 0035_client_report_links
Create Date: 2026-07-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0036_client_report_prose"
down_revision = "0035_client_report_links"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_report_prose",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_consultant_id", sa.Uuid(), nullable=False),
        sa.Column("deliverable_id", sa.Uuid(), nullable=False),
        sa.Column("sections_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_consultant_id"], ["consultants.id"]),
        sa.ForeignKeyConstraint(["deliverable_id"], ["deliverables.id"]),
        # A deliverable has exactly one client report, so saving is an upsert, not an append.
        sa.UniqueConstraint("deliverable_id", name="uq_client_report_prose_deliverable"),
    )
    op.create_index(
        "ix_client_report_prose_owner", "client_report_prose", ["owner_consultant_id"]
    )
    op.create_index(
        "ix_client_report_prose_deliverable", "client_report_prose", ["deliverable_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_client_report_prose_deliverable", table_name="client_report_prose")
    op.drop_index("ix_client_report_prose_owner", table_name="client_report_prose")
    op.drop_table("client_report_prose")
