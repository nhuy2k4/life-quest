"""Squashed: is_verified column now included in init_db (0001).
Kept as idempotent no-op to preserve revision chain.

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


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    # Guard: skip if already created by updated init_db
    if not _column_exists("users", "is_verified"):
        op.add_column(
            "users",
            sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade() -> None:
    if _column_exists("users", "is_verified"):
        op.drop_column("users", "is_verified")
