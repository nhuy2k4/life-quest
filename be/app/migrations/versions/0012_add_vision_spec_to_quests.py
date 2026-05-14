"""Add vision_spec to quests

Revision ID: 0012_add_vision_spec_to_quests
Revises: 0011_schema_hardening
Create Date: 2026-05-05 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0012_add_vision_spec_to_quests"
down_revision = "0011_schema_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("quests", sa.Column("vision_spec", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("quests", "vision_spec")
