"""audit_events

GRS-0032: append-only audit log. One table, audit_events — who did what to which resource, when.
Inserted, never updated or deleted; survives a subject's GDPR deletion as a de-identified compliance
record (the actor id is an opaque key once the person's PII is stripped).

Revision ID: 0018_audit_events
Revises: 0017_predictions_benchmark
Create Date: 2026-07-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0018_audit_events"
down_revision = "0017_predictions_benchmark"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("actor_consultant_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=48), nullable=False),
        sa.Column("resource_type", sa.String(length=48), nullable=True),
        sa.Column("resource_id", sa.Uuid(), nullable=True),
        sa.Column("detail", sa.String(length=500), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_audit_events_actor_consultant_id",
        "audit_events",
        ["actor_consultant_id"],
        unique=False,
    )
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"], unique=False)


def downgrade() -> None:
    op.drop_table("audit_events")
