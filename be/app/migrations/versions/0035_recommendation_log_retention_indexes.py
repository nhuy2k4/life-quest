"""Add recommendation log retention indexes

Revision ID: 0035_reco_log_retention_indexes
Revises: 0034_drop_user_quest_stats
Create Date: 2026-05-22 00:00:00.000000
"""

from alembic import op


revision = "0035_reco_log_retention_indexes"
down_revision = "0034_drop_user_quest_stats"
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.create_index(
		"ix_recommendation_logs_created_at",
		"recommendation_logs",
		["created_at"],
		unique=False,
	)
	op.create_index(
		"ix_recommendation_logs_user_event_created",
		"recommendation_logs",
		["user_id", "event", "created_at"],
		unique=False,
	)


def downgrade() -> None:
	op.drop_index("ix_recommendation_logs_user_event_created", table_name="recommendation_logs")
	op.drop_index("ix_recommendation_logs_created_at", table_name="recommendation_logs")
