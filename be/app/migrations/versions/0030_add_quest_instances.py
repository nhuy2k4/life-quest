"""Add quest_instances

Revision ID: 0030_add_quest_instances
Revises: f91a395ba849
Create Date: 2026-05-20 10:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0030_add_quest_instances"
down_revision = "f91a395ba849"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quest_instances",
        sa.Column("quest_id", UUID(as_uuid=True), sa.ForeignKey("quests.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("poi_id", UUID(as_uuid=True), sa.ForeignKey("pois.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_quest_instances_user_id", "quest_instances", ["user_id"])
    op.create_index("ix_quest_instances_quest_id", "quest_instances", ["quest_id"])
    op.create_index("ix_quest_instances_poi_id", "quest_instances", ["poi_id"])


def downgrade() -> None:
    op.drop_index("ix_quest_instances_poi_id", table_name="quest_instances")
    op.drop_index("ix_quest_instances_quest_id", table_name="quest_instances")
    op.drop_index("ix_quest_instances_user_id", table_name="quest_instances")
    op.drop_table("quest_instances")
