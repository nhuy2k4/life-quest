"""Add admin_adjust xp source

Revision ID: 0021_add_xp_source_admin_adjust
Revises: 0020_social_tables
Create Date: 2026-05-12 00:00:00.000000
"""

from alembic import op

revision = "0021_add_xp_source_admin_adjust"
down_revision = "0020_social_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE xp_source_enum ADD VALUE IF NOT EXISTS 'admin_adjust'")


def downgrade() -> None:
    # No downgrade for enum value removal in Postgres.
    pass
