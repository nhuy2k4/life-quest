"""Add is_event to quests

Revision ID: 0054_add_is_event_to_quests
Revises: 0053_add_quest_image_url
Create Date: 2026-06-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0054_add_is_event_to_quests"
down_revision = "0053_add_quest_image_url"
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.add_column("quests", sa.Column("is_event", sa.Boolean(), nullable=False, server_default=sa.text('false')))


def downgrade() -> None:
	op.drop_column("quests", "is_event")
