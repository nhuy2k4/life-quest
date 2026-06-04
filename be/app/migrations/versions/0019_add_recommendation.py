"""Add ML fields to recommendation logs

Revision ID: 0019_add_recommendation_log_ml_fields
Revises: 0018_recommendation_v2_tables
Create Date: 2026-05-07 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0019_add_recommendation"
down_revision = "0018_recommendation_v2_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("recommendation_logs", sa.Column("features_snapshot", sa.JSON(), nullable=True))
    op.add_column("recommendation_logs", sa.Column("rule_score", sa.Float(), nullable=True))
    op.add_column("recommendation_logs", sa.Column("ml_score", sa.Float(), nullable=True))
    op.add_column("recommendation_logs", sa.Column("final_score", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("recommendation_logs", "final_score")
    op.drop_column("recommendation_logs", "ml_score")
    op.drop_column("recommendation_logs", "rule_score")
    op.drop_column("recommendation_logs", "features_snapshot")
