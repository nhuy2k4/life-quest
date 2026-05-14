"""Add recommendation v2 tables

Revision ID: 0018_recommendation_v2_tables
Revises: 0017_seed_ai_quests
Create Date: 2026-05-07 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0018_recommendation_v2_tables"
down_revision = "0017_seed_ai_quests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recommendation_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quest_id", UUID(as_uuid=True), sa.ForeignKey("quests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event", sa.String(30), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("request_id", UUID(as_uuid=True), nullable=False),
        sa.Column("algorithm_version", sa.String(50), nullable=False, server_default=sa.text("'v2_mvp'")),
        sa.Column("reasons", sa.JSON(), nullable=True),
        sa.Column("score_breakdown", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reco_logs_user_created", "recommendation_logs", ["user_id", "created_at"])
    op.create_index("ix_reco_logs_request", "recommendation_logs", ["request_id"])
    op.create_index("ix_reco_logs_quest", "recommendation_logs", ["quest_id"])
    op.create_index("ix_reco_logs_event", "recommendation_logs", ["event"])

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
        sa.UniqueConstraint("quest_id", "stat_date", name="uq_quest_stats_daily_quest_date"),
    )
    op.create_index("ix_quest_stats_daily_quest", "quest_stats_daily", ["quest_id"])

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
    op.create_index("ix_user_quest_stats_user", "user_quest_stats", ["user_id"])

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
        sa.UniqueConstraint("user_id", name="uq_user_ai_stats_user"),
    )
    op.create_index("ix_user_ai_stats_user", "user_ai_stats", ["user_id"])

    op.create_table(
        "trending_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("quest_id", UUID(as_uuid=True), sa.ForeignKey("quests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("window", sa.String(20), nullable=False),
        sa.Column("score", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("quest_id", "window", name="uq_trending_scores_quest_window"),
    )
    op.create_index("ix_trending_scores_quest", "trending_scores", ["quest_id"])
    op.create_index("ix_trending_scores_window", "trending_scores", ["window"])


def downgrade() -> None:
    op.drop_index("ix_trending_scores_window", table_name="trending_scores")
    op.drop_index("ix_trending_scores_quest", table_name="trending_scores")
    op.drop_table("trending_scores")

    op.drop_index("ix_user_ai_stats_user", table_name="user_ai_stats")
    op.drop_table("user_ai_stats")

    op.drop_index("ix_user_quest_stats_user", table_name="user_quest_stats")
    op.drop_table("user_quest_stats")

    op.drop_index("ix_quest_stats_daily_quest", table_name="quest_stats_daily")
    op.drop_table("quest_stats_daily")

    op.drop_index("ix_reco_logs_event", table_name="recommendation_logs")
    op.drop_index("ix_reco_logs_quest", table_name="recommendation_logs")
    op.drop_index("ix_reco_logs_request", table_name="recommendation_logs")
    op.drop_index("ix_reco_logs_user_created", table_name="recommendation_logs")
    op.drop_table("recommendation_logs")
