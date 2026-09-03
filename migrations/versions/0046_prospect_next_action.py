"""A prospect's next action, and when it is due (GRS-0249 scope 4).

The pipeline had nowhere to record the one thing that has to happen next. That is the field a voice
note most obviously fills — "I told them we'd send the revised fee schedule by Friday" — and it is
also the judgement the Sales Ops course already teaches: a deal with no dated next action is
drifting.

The two columns are **independently nullable**. An action with no date is honest — the advisor
knows what to do and not yet when — and inventing a date to fill the column would be the
fabrication non-negotiable #3 exists to prevent. `next_action_on` is indexed because "what is due
this week, across my pipeline" is the question it will be asked.

Revision ID: 0046_prospect_next_action
Revises: 0045_voice_note_consent_and_parents
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0046_prospect_next_action"
down_revision = "0045_voice_note_consent_and_parents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("prospects", sa.Column("next_action", sa.String(length=280), nullable=True))
    op.add_column("prospects", sa.Column("next_action_on", sa.Date(), nullable=True))
    op.create_index("ix_prospects_next_action_on", "prospects", ["next_action_on"])


def downgrade() -> None:
    op.drop_index("ix_prospects_next_action_on", table_name="prospects")
    op.drop_column("prospects", "next_action_on")
    op.drop_column("prospects", "next_action")
