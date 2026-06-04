import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
	from app.models.user import User


class Conversation(Base, UUIDMixin, TimestampMixin):
	__tablename__ = "conversations"
	__table_args__ = (
		UniqueConstraint("user_one_id", "user_two_id", name="uq_conversations_pair"),
		Index("ix_conversations_user_one", "user_one_id"),
		Index("ix_conversations_user_two", "user_two_id"),
	)

	user_one_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		nullable=False,
	)
	user_two_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		nullable=False,
	)
	last_message_id: Mapped[uuid.UUID | None] = mapped_column(
		ForeignKey("messages.id", ondelete="SET NULL", use_alter=True),
		nullable=True,
	)
	last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

	user_one: Mapped["User"] = relationship("User", foreign_keys=[user_one_id])
	user_two: Mapped["User"] = relationship("User", foreign_keys=[user_two_id])
	messages: Mapped[list["Message"]] = relationship(
		"Message",
		back_populates="conversation",
		cascade="all, delete-orphan",
		foreign_keys="Message.conversation_id",
	)
	last_message: Mapped["Message | None"] = relationship("Message", foreign_keys=[last_message_id], post_update=True)


class Message(Base, UUIDMixin):
	__tablename__ = "messages"
	__table_args__ = (
		Index("ix_messages_conversation_created", "conversation_id", "created_at"),
		Index("ix_messages_sender", "sender_id"),
	)

	conversation_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("conversations.id", ondelete="CASCADE"),
		nullable=False,
	)
	sender_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		nullable=False,
	)
	content: Mapped[str] = mapped_column(Text, nullable=False)
	message_type: Mapped[str] = mapped_column(String(20), nullable=False, default="text")
	read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		nullable=False,
	)

	conversation: Mapped["Conversation"] = relationship(
		"Conversation",
		back_populates="messages",
		foreign_keys=[conversation_id],
	)
	sender: Mapped["User"] = relationship("User")
