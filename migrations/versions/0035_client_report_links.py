"""client_report_links + report_read_events

GRS-0220: the client report as a shared web page, with disclosed read tracking.

`client_report_links` snapshots the assembled report as JSON and stores only the SHA-256 of each
token. The plaintext is returned once, when the link is issued, and is unrecoverable afterwards — so
a leaked backup yields no working links. The hash is unique and indexed because resolving a
link is a hash lookup on every public request. The snapshot is what makes a shared link show
what was SHARED: re-rendering from live data would silently change a document the client has
already read.

`report_read_events` is append-only and deliberately narrow: link, section, dwell, when. No IP, no
user agent, no fingerprint. The page carries a visible notice that the sender can see which sections
were opened, and the shape of this table is what makes that notice truthful rather than partial.

Revision ID: 0035_client_report_links
Revises: 0034_section_test_attempts
Create Date: 2026-07-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0035_client_report_links"
down_revision = "0034_section_test_attempts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "client_report_links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("owner_consultant_id", sa.Uuid(), nullable=False),
        sa.Column("deliverable_id", sa.Uuid(), nullable=False),
        sa.Column("engagement_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("recipient_label", sa.String(length=200), nullable=False),
        # The assembled report, snapshotted at issue — a shared link shows what was shared.
        sa.Column("report_json", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        # Set once, never cleared. Un-revoking would resurrect a link the advisor has already told a
        # client is dead; issuing a fresh one is the way back.
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_viewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_consultant_id"], ["consultants.id"]),
        sa.ForeignKeyConstraint(["deliverable_id"], ["deliverables.id"]),
        sa.ForeignKeyConstraint(["engagement_id"], ["engagements.id"]),
        sa.UniqueConstraint("token_hash", name="uq_client_report_links_token_hash"),
    )
    op.create_index(
        "ix_client_report_links_owner_consultant_id",
        "client_report_links",
        ["owner_consultant_id"],
    )
    op.create_index(
        "ix_client_report_links_deliverable_id", "client_report_links", ["deliverable_id"]
    )
    op.create_index("ix_client_report_links_token_hash", "client_report_links", ["token_hash"])

    op.create_table(
        "report_read_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("link_id", sa.Uuid(), nullable=False),
        sa.Column("section", sa.String(length=40), nullable=False),
        sa.Column("dwell_ms", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        # `created_at` only: the table is append-only, and an `updated_at` would advertise a
        # mutation that never happens.
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["link_id"], ["client_report_links.id"]),
    )
    op.create_index("ix_report_read_events_link_id", "report_read_events", ["link_id"])
    op.create_index(
        "ix_report_read_events_link_section", "report_read_events", ["link_id", "section"]
    )


def downgrade() -> None:
    op.drop_index("ix_report_read_events_link_section", table_name="report_read_events")
    op.drop_index("ix_report_read_events_link_id", table_name="report_read_events")
    op.drop_table("report_read_events")
    op.drop_index("ix_client_report_links_token_hash", table_name="client_report_links")
    op.drop_index("ix_client_report_links_deliverable_id", table_name="client_report_links")
    op.drop_index("ix_client_report_links_owner_consultant_id", table_name="client_report_links")
    op.drop_table("client_report_links")
