"""Add user profile fields

Revision ID: 0026_add_user_profile_fields
Revises: 0025_add_user_push_tokens
Create Date: 2026-05-17 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "0026_add_user_profile_fields"
down_revision = "0025_add_user_push_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_name", sa.String(length=80), nullable=True))
    op.add_column("users", sa.Column("bio", sa.String(length=150), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "bio")
    op.drop_column("users", "display_name")
