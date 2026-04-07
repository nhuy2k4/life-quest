"""Convert fixed-value string columns to PostgreSQL enums

Revision ID: 0009_string_to_enum
Revises: 0008_interests_json
Create Date: 2026-04-07 23:15:00.000000
"""

from alembic import op


revision = "0009_string_to_enum"
down_revision = "0008_interests_json"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE user_role_enum AS ENUM ('user', 'admin')")
    op.execute("CREATE TYPE auth_provider_enum AS ENUM ('local', 'google')")
    op.execute("CREATE TYPE quest_difficulty_enum AS ENUM ('easy', 'medium', 'hard')")
    op.execute(
        "CREATE TYPE user_quest_status_enum AS ENUM ('not_started', 'started', 'submitted', 'approved', 'rejected', 'in_progress')"
    )
    op.execute(
        "CREATE TYPE submission_status_enum AS ENUM ('pending', 'approved', 'rejected', 'manual_review')"
    )
    op.execute("CREATE TYPE activity_level_enum AS ENUM ('low', 'medium', 'high')")
    op.execute("CREATE TYPE xp_source_enum AS ENUM ('quest_approved')")

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role DROP DEFAULT,
        ALTER COLUMN provider DROP DEFAULT
    """)

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role TYPE user_role_enum USING role::user_role_enum,
        ALTER COLUMN provider TYPE auth_provider_enum USING provider::auth_provider_enum
    """)

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role SET DEFAULT 'user'::user_role_enum,
        ALTER COLUMN provider SET DEFAULT 'local'::auth_provider_enum
    """)

    op.execute("ALTER TABLE quests ALTER COLUMN difficulty DROP DEFAULT")
    op.execute(
        "ALTER TABLE quests ALTER COLUMN difficulty TYPE quest_difficulty_enum USING difficulty::quest_difficulty_enum"
    )
    op.execute("ALTER TABLE quests ALTER COLUMN difficulty SET DEFAULT 'medium'::quest_difficulty_enum")

    op.execute("ALTER TABLE user_quests ALTER COLUMN status DROP DEFAULT")
    op.execute("UPDATE user_quests SET status='started' WHERE status='in_progress'")
    op.execute(
        "ALTER TABLE user_quests ALTER COLUMN status TYPE user_quest_status_enum USING status::user_quest_status_enum"
    )
    op.execute("ALTER TABLE user_quests ALTER COLUMN status SET DEFAULT 'started'::user_quest_status_enum")

    op.execute("ALTER TABLE submissions ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE submissions ALTER COLUMN status TYPE submission_status_enum USING status::submission_status_enum"
    )
    op.execute("ALTER TABLE submissions ALTER COLUMN status SET DEFAULT 'pending'::submission_status_enum")

    op.execute("ALTER TABLE user_preferences ALTER COLUMN activity_level TYPE activity_level_enum USING activity_level::activity_level_enum")

    op.execute("ALTER TABLE xp_transactions ALTER COLUMN source DROP DEFAULT")
    op.execute("UPDATE xp_transactions SET source='quest_approved' WHERE source NOT IN ('quest_approved')")
    op.execute(
        "ALTER TABLE xp_transactions ALTER COLUMN source TYPE xp_source_enum USING source::xp_source_enum"
    )
    op.execute("ALTER TABLE xp_transactions ALTER COLUMN source SET DEFAULT 'quest_approved'::xp_source_enum")


def downgrade() -> None:
    op.execute("ALTER TABLE xp_transactions ALTER COLUMN source DROP DEFAULT")
    op.execute("ALTER TABLE xp_transactions ALTER COLUMN source TYPE varchar(50) USING source::text")
    op.execute("ALTER TABLE xp_transactions ALTER COLUMN source SET DEFAULT 'quest_approved'")

    op.execute("ALTER TABLE user_preferences ALTER COLUMN activity_level TYPE varchar(20) USING activity_level::text")

    op.execute("ALTER TABLE submissions ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE submissions ALTER COLUMN status TYPE varchar(20) USING status::text")
    op.execute("ALTER TABLE submissions ALTER COLUMN status SET DEFAULT 'pending'")

    op.execute("ALTER TABLE user_quests ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE user_quests ALTER COLUMN status TYPE varchar(20) USING status::text")
    op.execute("ALTER TABLE user_quests ALTER COLUMN status SET DEFAULT 'started'")

    op.execute("ALTER TABLE quests ALTER COLUMN difficulty DROP DEFAULT")
    op.execute("ALTER TABLE quests ALTER COLUMN difficulty TYPE varchar(20) USING difficulty::text")
    op.execute("ALTER TABLE quests ALTER COLUMN difficulty SET DEFAULT 'medium'")

    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role DROP DEFAULT,
        ALTER COLUMN provider DROP DEFAULT
    """)
    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role TYPE varchar(20) USING role::text,
        ALTER COLUMN provider TYPE varchar(20) USING provider::text
    """)
    op.execute("""
        ALTER TABLE users
        ALTER COLUMN role SET DEFAULT 'user',
        ALTER COLUMN provider SET DEFAULT 'local'
    """)

    op.execute("DROP TYPE IF EXISTS xp_source_enum")
    op.execute("DROP TYPE IF EXISTS activity_level_enum")
    op.execute("DROP TYPE IF EXISTS submission_status_enum")
    op.execute("DROP TYPE IF EXISTS user_quest_status_enum")
    op.execute("DROP TYPE IF EXISTS quest_difficulty_enum")
    op.execute("DROP TYPE IF EXISTS auth_provider_enum")
    op.execute("DROP TYPE IF EXISTS user_role_enum")
