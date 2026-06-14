"""Add quest image URL

Revision ID: 0053_add_quest_image_url
Revises: 0052_drop_rejection_reason_expires_at
Create Date: 2026-06-13

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0053_add_quest_image_url"
down_revision = "0052_drop_rejection_reason_expires_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.add_column("quests", sa.Column("image_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
	op.drop_column("quests", "image_url")