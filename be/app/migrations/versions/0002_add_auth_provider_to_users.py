"""Squashed: provider and provider_id columns now included in init_db (0001).
This migration is kept as a no-op to preserve the revision chain for
environments that ran an older version of 0001 without provider columns.

Revision ID: 0002_add_auth_provider_to_users
Revises: 0001_initial_tables
Create Date: 2026-04-06 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "0002_add_auth_provider_to_users"
down_revision = "0001_initial_tables"
branch_labels = None
depends_on = None


def _column_exists(table: str, column: str) -> bool:
    """Check if a column already exists (idempotent guard)."""
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    )
    return result.fetchone() is not None


def _index_exists(index_name: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM pg_indexes WHERE indexname = :i"
        ),
        {"i": index_name},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    # Guard: skip if columns already exist (created by updated init_db)
    if not _column_exists("users", "provider"):
        op.add_column(
            "users",
            sa.Column("provider", sa.String(length=20), nullable=False, server_default="local"),
        )
    if not _column_exists("users", "provider_id"):
        op.add_column(
            "users",
            sa.Column("provider_id", sa.String(length=255), nullable=True),
        )
    if not _index_exists("ix_users_provider_id"):
        op.create_index("ix_users_provider_id", "users", ["provider_id"])

    op.execute("UPDATE users SET provider = 'local' WHERE provider IS NULL")

    # Make password_hash nullable if it isn't already
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=True,
    )


def downgrade() -> None:
    op.execute("UPDATE users SET password_hash = '' WHERE password_hash IS NULL")
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(length=255),
        nullable=False,
    )
    if _index_exists("ix_users_provider_id"):
        op.drop_index("ix_users_provider_id", table_name="users")
    if _column_exists("users", "provider_id"):
        op.drop_column("users", "provider_id")
    if _column_exists("users", "provider"):
        op.drop_column("users", "provider")
