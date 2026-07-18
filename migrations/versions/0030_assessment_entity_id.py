"""assessment_entity_id

GRS-0100 (ADR-0033): an assessment subject can resolve to a canonical company. Adds a nullable,
indexed `entity_id` on assessments (null = manual/unlinked). Two assessments of the same company
share this id, so dedup is a cheap owner-scoped query.

Revision ID: 0030_assessment_entity_id
Revises: 0029_contacts_and_prospect_website
Create Date: 2026-07-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0030_assessment_entity_id"
down_revision = "0029_contacts_and_prospect_website"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("assessments", sa.Column("entity_id", sa.String(length=128), nullable=True))
    op.create_index("ix_assessments_entity_id", "assessments", ["entity_id"])


def downgrade() -> None:
    op.drop_index("ix_assessments_entity_id", table_name="assessments")
    op.drop_column("assessments", "entity_id")
