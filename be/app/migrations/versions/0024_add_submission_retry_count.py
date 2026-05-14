"""Add submission retry count

Revision ID: 0024_add_submission_retry_count
Revises: 0023_add_post_direct_quest_id
Create Date: 2026-05-14 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0024_add_submission_retry_count"
down_revision = "0023_add_post_direct_quest_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "submissions",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("submissions", "retry_count", server_default=None)


def downgrade() -> None:
    op.drop_column("submissions", "retry_count")
