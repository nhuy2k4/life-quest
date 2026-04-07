"""Drop legacy in_progress from user_quest status enum

Revision ID: 0010_drop_legacy_status
Revises: 0009_string_to_enum
Create Date: 2026-04-07 23:45:00.000000
"""

from alembic import op


revision = "0010_drop_legacy_status"
down_revision = "0009_string_to_enum"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE user_quests SET status='started' WHERE status='in_progress'")

    op.execute(
        "CREATE TYPE user_quest_status_enum_new AS ENUM ('not_started', 'started', 'submitted', 'approved', 'rejected')"
    )
    op.execute("ALTER TABLE user_quests ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE user_quests ALTER COLUMN status TYPE user_quest_status_enum_new USING status::text::user_quest_status_enum_new"
    )
    op.execute("ALTER TABLE user_quests ALTER COLUMN status SET DEFAULT 'started'::user_quest_status_enum_new")

    op.execute("DROP TYPE user_quest_status_enum")
    op.execute("ALTER TYPE user_quest_status_enum_new RENAME TO user_quest_status_enum")


def downgrade() -> None:
    op.execute(
        "CREATE TYPE user_quest_status_enum_old AS ENUM ('not_started', 'started', 'submitted', 'approved', 'rejected', 'in_progress')"
    )
    op.execute("ALTER TABLE user_quests ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE user_quests ALTER COLUMN status TYPE user_quest_status_enum_old USING status::text::user_quest_status_enum_old"
    )
    op.execute("ALTER TABLE user_quests ALTER COLUMN status SET DEFAULT 'started'::user_quest_status_enum_old")

    op.execute("DROP TYPE user_quest_status_enum")
    op.execute("ALTER TYPE user_quest_status_enum_old RENAME TO user_quest_status_enum")
