"""Drop poi fields from quests

Revision ID: 0031_drop_quest_poi_fields
Revises: 0030_add_quest_instances
Create Date: 2026-05-20 11:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0031_drop_quest_poi_fields"
down_revision = "0030_add_quest_instances"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_quests_poi_id")

    op.execute("""
        ALTER TABLE quests
        DROP CONSTRAINT IF EXISTS quests_poi_id_fkey
    """)

    op.execute("""
        ALTER TABLE quests
        DROP COLUMN IF EXISTS poi_id
    """)

    op.execute("""
        ALTER TABLE quests
        DROP COLUMN IF EXISTS poi_required
    """)


def downgrade() -> None:
    op.add_column(
        "quests",
        sa.Column(
            "poi_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column("quests", sa.Column("poi_id", sa.UUID(), nullable=True))
    op.create_index("ix_quests_poi_id", "quests", ["poi_id"])