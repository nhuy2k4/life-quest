"""Add poi_id to posts

Revision ID: 0044_add_poi_id_to_posts
Revises: 0042_add_avatar_url_to_users
Create Date: 2026-05-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "0044_add_poi_id_to_posts"
down_revision = "0042_add_avatar_url_to_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("posts", sa.Column("poi_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "posts_poi_id_fkey",
        "posts",
        "pois",
        ["poi_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_posts_poi_id", "posts", ["poi_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_posts_poi_id", table_name="posts")
    op.drop_constraint("posts_poi_id_fkey", "posts", type_="foreignkey")
    op.drop_column("posts", "poi_id")
