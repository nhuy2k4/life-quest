"""Drop unused recommendation and audit tables

Revision ID: 0028_drop_unused_reco_tables
Revises: 0027_reco_rule_categories
Create Date: 2026-05-17 00:10:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0028_drop_unused_reco_tables"
down_revision = "0027_reco_rule_categories"
branch_labels = None
depends_on = None


def upgrade() -> None:
	for table_name in (
		"user_ai_stats",
		"trending_scores",
		"quest_stats_daily",
		"reward_logs",
		"submission_reviews",
		"user_events",
	):
		op.drop_table(table_name)


def downgrade() -> None:
	op.create_table(
		"user_events",
		sa.Column("id", UUID(as_uuid=True), primary_key=True),
		sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
		sa.Column("event_name", sa.String(length=100), nullable=False),
		sa.Column("payload", sa.JSON(), nullable=True),
		sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
	)
	op.create_table(
		"submission_reviews",
		sa.Column("id", UUID(as_uuid=True), primary_key=True),
		sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
		sa.Column("reviewer_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
		sa.Column("decision", sa.String(length=30), nullable=False),
		sa.Column("note", sa.Text(), nullable=True),
		sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
	)
	op.create_table(
		"reward_logs",
		sa.Column("id", UUID(as_uuid=True), primary_key=True),
		sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submissions.id", ondelete="SET NULL"), nullable=True),
		sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
		sa.Column("reward_type", sa.String(length=30), nullable=False),
		sa.Column("amount", sa.Integer(), nullable=False, server_default=sa.text("0")),
		sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
	)
	op.create_table(
		"quest_stats_daily",
		sa.Column("id", UUID(as_uuid=True), primary_key=True),
		sa.Column("quest_id", UUID(as_uuid=True), sa.ForeignKey("quests.id", ondelete="CASCADE"), nullable=False),
		sa.Column("stat_date", sa.Date(), nullable=False),
		sa.Column("shown", sa.Integer(), nullable=False, server_default=sa.text("0")),
		sa.Column("clicked", sa.Integer(), nullable=False, server_default=sa.text("0")),
		sa.Column("started", sa.Integer(), nullable=False, server_default=sa.text("0")),
		sa.Column("completed", sa.Integer(), nullable=False, server_default=sa.text("0")),
		sa.Column("ignored", sa.Integer(), nullable=False, server_default=sa.text("0")),
		sa.Column("completion_rate", sa.Float(), nullable=False, server_default=sa.text("0")),
		sa.Column("avg_completion_time_s", sa.Float(), nullable=True),
		sa.Column("popularity_score", sa.Float(), nullable=False, server_default=sa.text("0")),
		sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
	)
	op.create_table(
		"trending_scores",
		sa.Column("id", UUID(as_uuid=True), primary_key=True),
		sa.Column("quest_id", UUID(as_uuid=True), sa.ForeignKey("quests.id", ondelete="CASCADE"), nullable=False),
		sa.Column("window", sa.String(length=20), nullable=False),
		sa.Column("score", sa.Float(), nullable=False, server_default=sa.text("0")),
		sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
	)
	op.create_table(
		"user_ai_stats",
		sa.Column("id", UUID(as_uuid=True), primary_key=True),
		sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
		sa.Column("vision_success_rate", sa.Float(), nullable=False, server_default=sa.text("0")),
		sa.Column("poi_success_rate", sa.Float(), nullable=False, server_default=sa.text("0")),
		sa.Column("avg_confidence", sa.Float(), nullable=False, server_default=sa.text("0")),
		sa.Column("recent_fail_streak", sa.Integer(), nullable=False, server_default=sa.text("0")),
		sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
		sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
	)
