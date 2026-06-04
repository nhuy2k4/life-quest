"""Add post interactions to recommendation logs

Revision ID: 0036_reco_logs_post_id
Revises: 0035_reco_log_retention_indexes
Create Date: 2026-05-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "0036_reco_logs_post_id"
down_revision = "0035_reco_log_retention_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.alter_column(
		"recommendation_logs",
		"quest_id",
		existing_type=UUID(as_uuid=True),
		nullable=True,
	)
	op.add_column(
		"recommendation_logs",
		sa.Column("post_id", UUID(as_uuid=True), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=True),
	)
	op.create_index("ix_recommendation_logs_post_id", "recommendation_logs", ["post_id"], unique=False)


def downgrade() -> None:
	op.execute("DELETE FROM recommendation_logs WHERE quest_id IS NULL")
	op.drop_index("ix_recommendation_logs_post_id", table_name="recommendation_logs")
	op.drop_column("recommendation_logs", "post_id")
	op.alter_column(
		"recommendation_logs",
		"quest_id",
		existing_type=UUID(as_uuid=True),
		nullable=False,
	)
