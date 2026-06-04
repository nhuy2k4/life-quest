"""Add 1-1 chat tables

Revision ID: 0048_chat_1_1_tables
Revises: 0047_event_mvp_tables
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "0048_chat_1_1_tables"
down_revision = "0047_event_mvp_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.create_table(
		"conversations",
		sa.Column("id", UUID(as_uuid=True), primary_key=True),
		sa.Column("user_one_id", UUID(as_uuid=True), nullable=False),
		sa.Column("user_two_id", UUID(as_uuid=True), nullable=False),
		sa.Column("last_message_id", UUID(as_uuid=True), nullable=True),
		sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
		sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
		sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
		sa.ForeignKeyConstraint(["user_one_id"], ["users.id"], ondelete="CASCADE"),
		sa.ForeignKeyConstraint(["user_two_id"], ["users.id"], ondelete="CASCADE"),
		sa.UniqueConstraint("user_one_id", "user_two_id", name="uq_conversations_pair"),
	)
	op.create_index("ix_conversations_user_one", "conversations", ["user_one_id"], unique=False)
	op.create_index("ix_conversations_user_two", "conversations", ["user_two_id"], unique=False)

	op.create_table(
		"messages",
		sa.Column("id", UUID(as_uuid=True), primary_key=True),
		sa.Column("conversation_id", UUID(as_uuid=True), nullable=False),
		sa.Column("sender_id", UUID(as_uuid=True), nullable=False),
		sa.Column("content", sa.Text(), nullable=False),
		sa.Column("message_type", sa.String(length=20), nullable=False, server_default="text"),
		sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
		sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
		sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
		sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
	)
	op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at"], unique=False)
	op.create_index("ix_messages_sender", "messages", ["sender_id"], unique=False)
	op.create_foreign_key(
		"conversations_last_message_id_fkey",
		"conversations",
		"messages",
		["last_message_id"],
		["id"],
		ondelete="SET NULL",
	)


def downgrade() -> None:
	op.drop_constraint("conversations_last_message_id_fkey", "conversations", type_="foreignkey")
	op.drop_index("ix_messages_sender", table_name="messages")
	op.drop_index("ix_messages_conversation_created", table_name="messages")
	op.drop_table("messages")
	op.drop_index("ix_conversations_user_two", table_name="conversations")
	op.drop_index("ix_conversations_user_one", table_name="conversations")
	op.drop_table("conversations")
