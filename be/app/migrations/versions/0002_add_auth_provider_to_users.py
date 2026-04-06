"""Add provider fields to users for Google auth support

Revision ID: 0002_add_auth_provider_to_users
Revises: 0001_initial_tables
Create Date: 2026-04-06 10:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_auth_provider_to_users"
down_revision = "0001_initial_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("provider", sa.String(length=20), nullable=False, server_default="local"),
    )
    op.add_column(
        "users",
        sa.Column("provider_id", sa.String(length=255), nullable=True),
    )
    op.create_index("ix_users_provider_id", "users", ["provider_id"])

    # Backward-compatible: existing users are local accounts.
    op.execute("UPDATE users SET provider = 'local' WHERE provider IS NULL")

    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    # Ensure NOT NULL constraint can be restored safely.
    op.execute("UPDATE users SET password_hash = '' WHERE password_hash IS NULL")

    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=False,
    )

    op.drop_index("ix_users_provider_id", table_name="users")
    op.drop_column("users", "provider_id")
    op.drop_column("users", "provider")
