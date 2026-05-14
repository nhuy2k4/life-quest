"""Add user push tokens

Revision ID: 0025_add_user_push_tokens
Revises: 0024_add_submission_retry_count
Create Date: 2026-05-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0025_add_user_push_tokens"
down_revision = "0024_add_submission_retry_count"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_push_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False, server_default="expo"),
        sa.Column("platform", sa.String(30), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("token", name="uq_user_push_tokens_token"),
    )
    op.create_index("ix_user_push_tokens_user_id", "user_push_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_push_tokens_user_id", table_name="user_push_tokens")
    op.drop_table("user_push_tokens")
