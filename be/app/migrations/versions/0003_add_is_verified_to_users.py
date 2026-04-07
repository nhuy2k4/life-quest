"""Add is_verified to users for email OTP verification

Revision ID: 0003_add_is_verified_to_users
Revises: 0002_add_auth_provider_to_users
Create Date: 2026-04-06 12:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "0003_add_is_verified_to_users"
down_revision = "0002_add_auth_provider_to_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("users", "is_verified")
