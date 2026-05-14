"""Add poi_required and ai_metadata

Revision ID: 0016_poi_required_ai_metadata
Revises: 0015_pois_external_id_not_null
Create Date: 2026-05-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0016_poi_required_ai_metadata"
down_revision = "0015_pois_external_id_not_null"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("quests", sa.Column("poi_required", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("submissions", sa.Column("ai_metadata", sa.JSON(), nullable=True))
    op.alter_column("quests", "min_confidence", server_default=sa.text("0.5"))


def downgrade() -> None:
    op.alter_column("quests", "min_confidence", server_default=None)
    op.drop_column("submissions", "ai_metadata")
    op.drop_column("quests", "poi_required")
