"""Add standalone post fields image_url and caption

Revision ID: 0022_add_standalone_post_fields
Revises: 0021_add_xp_source_admin_adjust
Create Date: 2026-05-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0022_add_standalone_post_fields"
down_revision = "0021_add_xp_source_admin_adjust"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("image_url", sa.Text(), nullable=True))
    op.add_column("posts", sa.Column("caption", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("posts", "caption")
    op.drop_column("posts", "image_url")
