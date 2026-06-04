import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.models.enums import EventStatus, sql_enum

if TYPE_CHECKING:
	from app.models.badge import Badge
	from app.models.quest import Quest
	from app.models.social import Post
	from app.models.user import User


class Event(Base, UUIDMixin, TimestampMixin):
	__tablename__ = "events"

	title: Mapped[str] = mapped_column(String(255), nullable=False)
	description: Mapped[str | None] = mapped_column(Text, nullable=True)
	banner_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
	start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
	status: Mapped[EventStatus] = mapped_column(
		sql_enum(EventStatus, name="event_status_enum"),
		nullable=False,
		default=EventStatus.DRAFT,
	)
	reward_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
	created_by: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="SET NULL"),
		nullable=True,
		index=True,
	)

	quests: Mapped[list["Quest"]] = relationship(
		"Quest",
		secondary="event_quests",
		back_populates="events",
	)
	posts: Mapped[list["Post"]] = relationship("Post", back_populates="event")
	results: Mapped[list["EventResult"]] = relationship(
		"EventResult",
		back_populates="event",
		cascade="all, delete-orphan",
	)
	creator: Mapped["User | None"] = relationship("User")


class EventQuest(Base):
	__tablename__ = "event_quests"

	event_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("events.id", ondelete="CASCADE"),
		primary_key=True,
	)
	quest_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("quests.id", ondelete="CASCADE"),
		primary_key=True,
	)


class EventResult(Base, UUIDMixin):
	__tablename__ = "event_results"

	event_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("events.id", ondelete="CASCADE"),
		nullable=False,
		index=True,
	)
	user_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		nullable=False,
		index=True,
	)
	post_id: Mapped[uuid.UUID | None] = mapped_column(
		ForeignKey("posts.id", ondelete="SET NULL"),
		nullable=True,
	)
	total_likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
	rank: Mapped[int] = mapped_column(Integer, nullable=False)
	bonus_xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
	badge_id: Mapped[uuid.UUID | None] = mapped_column(
		ForeignKey("badges.id", ondelete="SET NULL"),
		nullable=True,
	)
	awarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		nullable=False,
	)

	event: Mapped["Event"] = relationship("Event", back_populates="results")
	post: Mapped["Post | None"] = relationship("Post")
	badge: Mapped["Badge | None"] = relationship("Badge")
	user: Mapped["User"] = relationship("User")
