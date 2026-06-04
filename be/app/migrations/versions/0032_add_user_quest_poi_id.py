"""Add poi_id to user_quests

Revision ID: 0032_add_user_quest_poi_id
Revises: 0031_drop_quest_poi_fields
Create Date: 2026-05-20 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0032_add_user_quest_poi_id"
down_revision = "0031_drop_quest_poi_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE user_quests
        ADD COLUMN IF NOT EXISTS poi_id UUID
    """)

    op.execute("""
        ALTER TABLE user_quests
        DROP CONSTRAINT IF EXISTS uq_user_quests_user_quest
    """)

    op.execute("""
        ALTER TABLE user_quests
        DROP CONSTRAINT IF EXISTS user_quests_poi_id_fkey
    """)

    op.create_foreign_key(
        "user_quests_poi_id_fkey",
        "user_quests",
        "pois",
        ["poi_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_user_quests_user_quest_no_poi
        ON user_quests (user_id, quest_id)
        WHERE poi_id IS NULL
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_user_quests_user_quest_poi
        ON user_quests (user_id, quest_id, poi_id)
        WHERE poi_id IS NOT NULL
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_user_quests_poi_id
        ON user_quests (poi_id)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_user_quests_poi_id")
    op.execute("DROP INDEX IF EXISTS uq_user_quests_user_quest_poi")
    op.execute("DROP INDEX IF EXISTS uq_user_quests_user_quest_no_poi")

    op.execute("""
        ALTER TABLE user_quests
        DROP CONSTRAINT IF EXISTS user_quests_poi_id_fkey
    """)

    op.execute("""
        ALTER TABLE user_quests
        DROP COLUMN IF EXISTS poi_id
    """)

    op.create_unique_constraint(
        "uq_user_quests_user_quest",
        "user_quests",
        ["user_id", "quest_id"],
    )