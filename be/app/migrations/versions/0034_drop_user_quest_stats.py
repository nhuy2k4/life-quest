"""Drop unused user quest stats table

Revision ID: 0034_drop_user_quest_stats
Revises: 0033_backfill_quest_categories
Create Date: 2026-05-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "0034_drop_user_quest_stats"
down_revision = "0033_backfill_quest_categories"
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.execute("DROP TABLE IF EXISTS user_quest_stats")


def downgrade() -> None:
	op.create_table(
		"user_quest_stats",
		sa.Column("id", UUID(as_uuid=True), primary_key=True),
		sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
		sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
		sa.Column("started_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
		sa.Column("completed_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
		sa.Column("abandoned_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
		sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
		sa.Column("avg_completion_time_s", sa.Float(), nullable=True),
		sa.Column("completion_rate", sa.Float(), nullable=False, server_default=sa.text("0")),
		sa.Column("last_completed_at", sa.DateTime(timezone=True), nullable=True),
		sa.UniqueConstraint("user_id", "category_id", name="uq_user_quest_stats_user_category"),
	)
	op.create_index("ix_user_quest_stats_user_id", "user_quest_stats", ["user_id"])
	op.create_index("ix_user_quest_stats_category_id", "user_quest_stats", ["category_id"])
