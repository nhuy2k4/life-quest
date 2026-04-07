import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.models.enums import QuestDifficulty, sql_enum

if TYPE_CHECKING:
	from app.models.user_quest import UserQuest


class QuestCategory(Base):
	"""Bảng nối M:N giữa quest và category."""

	__tablename__ = "quest_categories"

	quest_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("quests.id", ondelete="CASCADE"),
		primary_key=True,
	)
	category_id: Mapped[int] = mapped_column(
		ForeignKey("categories.id", ondelete="CASCADE"),
		primary_key=True,
	)


class Category(Base):
	__tablename__ = "categories"

	id: Mapped[int] = mapped_column(primary_key=True)
	name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
	icon: Mapped[str | None] = mapped_column(String(100), nullable=True)

	quests: Mapped[list["Quest"]] = relationship(
		"Quest",
		secondary="quest_categories",
		back_populates="categories",
	)


class Quest(Base, UUIDMixin, TimestampMixin):
	__tablename__ = "quests"

	title: Mapped[str] = mapped_column(String(255), nullable=False)
	description: Mapped[str | None] = mapped_column(Text, nullable=True)
	xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
	difficulty: Mapped[QuestDifficulty] = mapped_column(
		sql_enum(QuestDifficulty, name="quest_difficulty_enum"),
		nullable=False,
		default=QuestDifficulty.MEDIUM,
	)
	approval_rate: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
	time_limit_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
	location_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
	is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

	categories: Mapped[list["Category"]] = relationship(
		"Category",
		secondary="quest_categories",
		back_populates="quests",
	)
	user_quests: Mapped[list["UserQuest"]] = relationship(
		"UserQuest",
		back_populates="quest",
		cascade="all, delete-orphan",
	)
