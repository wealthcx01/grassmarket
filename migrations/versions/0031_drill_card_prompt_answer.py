"""drill_card_prompt_answer

GRS-0139 (Academy learning loop): a drill card carries real retrieval content: the recall
question and the model answer — so it is a real flashcard, not a bare topic string. Existing
cards backfill to empty (a legacy topic-only card).

Revision ID: 0031_drill_card_prompt_answer
Revises: 0030_assessment_entity_id
Create Date: 2026-07-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0031_drill_card_prompt_answer"
down_revision = "0030_assessment_entity_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("drill_cards", sa.Column("prompt", sa.Text(), nullable=False, server_default=""))
    op.add_column("drill_cards", sa.Column("answer", sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("drill_cards", "answer")
    op.drop_column("drill_cards", "prompt")
