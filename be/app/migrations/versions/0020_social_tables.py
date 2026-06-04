"""Create social tables

Revision ID: 0020_social_tables
Revises: 0019_add_recommendation_log_ml_fields
Create Date: 2026-05-12 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0020_social_tables"
down_revision = "0019_add_recommendation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "follows",
        sa.Column("follower_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("following_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_follows_follower", "follows", ["follower_id"])
    op.create_index("ix_follows_following", "follows", ["following_id"])

    op.create_table(
        "posts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=True, unique=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_posts_user", "posts", ["user_id"])
    op.create_index("ix_posts_created", "posts", ["created_at"])

    op.create_table(
        "likes",
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("post_id", UUID(as_uuid=True), sa.ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_likes_user", "likes", ["user_id"])
    op.create_index("ix_likes_post", "likes", ["post_id"])

    op.create_table(
        "comments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("post_id", UUID(as_uuid=True), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("comments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_comments_post", "comments", ["post_id"])
    op.create_index("ix_comments_user", "comments", ["user_id"])
    op.create_index("ix_comments_parent", "comments", ["parent_id"])


def downgrade() -> None:
    op.drop_index("ix_comments_parent", table_name="comments")
    op.drop_index("ix_comments_user", table_name="comments")
    op.drop_index("ix_comments_post", table_name="comments")
    op.drop_table("comments")

    op.drop_index("ix_likes_post", table_name="likes")
    op.drop_index("ix_likes_user", table_name="likes")
    op.drop_table("likes")

    op.drop_index("ix_posts_created", table_name="posts")
    op.drop_index("ix_posts_user", table_name="posts")
    op.drop_table("posts")

    op.drop_index("ix_follows_following", table_name="follows")
    op.drop_index("ix_follows_follower", table_name="follows")
    op.drop_table("follows")
