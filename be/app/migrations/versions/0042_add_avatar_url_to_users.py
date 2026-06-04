"""Add avatar_url to users

Revision ID: 0042_add_avatar_url_to_users
Revises: 0041_reward_title_unique_user_badge
Create Date: 2026-05-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0042_add_avatar_url_to_users"
down_revision = "0041_reward_title_unique_user_badge"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_url", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_url")
