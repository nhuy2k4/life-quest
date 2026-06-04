"""Drop recommendation log reasons

Revision ID: 0038_drop_reco_log_reasons
Revises: 0037_simplify_reco_logs
Create Date: 2026-05-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0038_drop_reco_log_reasons"
down_revision = "0037_simplify_reco_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.drop_column("recommendation_logs", "reasons")


def downgrade() -> None:
	op.add_column("recommendation_logs", sa.Column("reasons", sa.JSON(), nullable=True))
