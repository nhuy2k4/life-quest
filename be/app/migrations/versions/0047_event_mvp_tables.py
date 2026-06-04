"""Add event MVP tables

Revision ID: 0047_event_mvp_tables
Revises: 0046_translate_quest_texts_to_english
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID


revision = "0047_event_mvp_tables"
down_revision = "0046_translate_quest_texts_to_english"
branch_labels = None
depends_on = None


event_status_enum = postgresql.ENUM(
	"draft",
	"active",
	"ended",
	name="event_status_enum",
	create_type=False,
)


def upgrade() -> None:
	op.execute(
		"""
		DO $$
		BEGIN
			IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'event_status_enum') THEN
				CREATE TYPE event_status_enum AS ENUM ('draft', 'active', 'ended');
			END IF;
		END
		$$;
		"""
	)
	op.execute("ALTER TYPE xp_source_enum ADD VALUE IF NOT EXISTS 'event_reward'")

	op.create_table(
		"events",
		sa.Column("id", UUID(as_uuid=True), primary_key=True),
		sa.Column("title", sa.String(length=255), nullable=False),
		sa.Column("description", sa.Text(), nullable=True),
		sa.Column("banner_url", sa.String(length=500), nullable=True),
		sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
		sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
		sa.Column("status", event_status_enum, nullable=False),
		sa.Column("reward_config", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
		sa.Column("created_by", UUID(as_uuid=True), nullable=True),
		sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
		sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
		sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
	)
	op.create_index("ix_events_created_by", "events", ["created_by"], unique=False)

	op.create_table(
		"event_quests",
		sa.Column("event_id", UUID(as_uuid=True), nullable=False),
		sa.Column("quest_id", UUID(as_uuid=True), nullable=False),
		sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
		sa.ForeignKeyConstraint(["quest_id"], ["quests.id"], ondelete="CASCADE"),
		sa.PrimaryKeyConstraint("event_id", "quest_id"),
	)

	op.add_column("posts", sa.Column("event_id", UUID(as_uuid=True), nullable=True))
	op.create_foreign_key(
		"posts_event_id_fkey",
		"posts",
		"events",
		["event_id"],
		["id"],
		ondelete="SET NULL",
	)
	op.create_index("ix_posts_event_id", "posts", ["event_id"], unique=False)

	op.create_table(
		"event_results",
		sa.Column("id", UUID(as_uuid=True), primary_key=True),
		sa.Column("event_id", UUID(as_uuid=True), nullable=False),
		sa.Column("user_id", UUID(as_uuid=True), nullable=False),
		sa.Column("post_id", UUID(as_uuid=True), nullable=True),
		sa.Column("total_likes", sa.Integer(), nullable=False, server_default=sa.text("0")),
		sa.Column("rank", sa.Integer(), nullable=False),
		sa.Column("bonus_xp", sa.Integer(), nullable=False, server_default=sa.text("0")),
		sa.Column("badge_id", UUID(as_uuid=True), nullable=True),
		sa.Column("awarded_at", sa.DateTime(timezone=True), nullable=True),
		sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
		sa.ForeignKeyConstraint(["badge_id"], ["badges.id"], ondelete="SET NULL"),
		sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
		sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="SET NULL"),
		sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
	)
	op.create_index("ix_event_results_event_id", "event_results", ["event_id"], unique=False)
	op.create_index("ix_event_results_user_id", "event_results", ["user_id"], unique=False)


def downgrade() -> None:
	op.drop_index("ix_event_results_user_id", table_name="event_results")
	op.drop_index("ix_event_results_event_id", table_name="event_results")
	op.drop_table("event_results")

	op.drop_index("ix_posts_event_id", table_name="posts")
	op.drop_constraint("posts_event_id_fkey", "posts", type_="foreignkey")
	op.drop_column("posts", "event_id")

	op.drop_table("event_quests")
	op.drop_index("ix_events_created_by", table_name="events")
	op.drop_table("events")
	op.execute("DROP TYPE event_status_enum")
