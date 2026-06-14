"""Simplify recommendation logs

Revision ID: 0037_simplify_reco_logs
Revises: 0036_reco_logs_post_id
Create Date: 2026-05-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0037_simplify_reco_logs"
down_revision = "0036_reco_logs_post_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
	for column_name in (
		"score_breakdown",
		"section",
	):
		op.drop_column("recommendation_logs", column_name)


def downgrade() -> None:
	op.add_column("recommendation_logs", sa.Column("section", sa.String(length=50), nullable=True))
	op.add_column("recommendation_logs", sa.Column("score_breakdown", sa.JSON(), nullable=True))
