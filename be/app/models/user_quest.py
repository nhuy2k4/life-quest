import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin
from app.models.enums import UserQuestStatus, sql_enum

if TYPE_CHECKING:
	from app.models.quest import Quest
	from app.models.poi import Poi
	from app.models.submission import Submission
	from app.models.user import User


STARTED_STATUSES = {UserQuestStatus.STARTED}
TERMINAL_STATUSES = {UserQuestStatus.APPROVED, UserQuestStatus.REJECTED}


class UserQuest(Base, UUIDMixin):
	__tablename__ = "user_quests"
	__table_args__ = (
		Index(
			"uq_user_quests_user_quest_no_poi",
			"user_id",
			"quest_id",
			unique=True,
			postgresql_where=text("poi_id IS NULL"),
			sqlite_where=text("poi_id IS NULL"),
		),
		Index(
			"uq_user_quests_user_quest_poi",
			"user_id",
			"quest_id",
			"poi_id",
			unique=True,
			postgresql_where=text("poi_id IS NOT NULL"),
			sqlite_where=text("poi_id IS NOT NULL"),
		),
	)

	user_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		nullable=False,
	)
	quest_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("quests.id", ondelete="CASCADE"),
		nullable=False,
	)
	poi_id: Mapped[uuid.UUID | None] = mapped_column(
		ForeignKey("pois.id", ondelete="SET NULL"),
		nullable=True,
	)
	status: Mapped[UserQuestStatus] = mapped_column(
		sql_enum(UserQuestStatus, name="user_quest_status_enum"),
		nullable=False,
		default=UserQuestStatus.STARTED,
	)
	started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	consolation_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

	user: Mapped["User"] = relationship("User")
	quest: Mapped["Quest"] = relationship("Quest", back_populates="user_quests")
	poi: Mapped["Poi | None"] = relationship("Poi")
	submission: Mapped["Submission | None"] = relationship(
		"Submission",
		back_populates="user_quest",
		uselist=False,
		cascade="all, delete-orphan",
	)

	@property
	def normalized_status(self) -> UserQuestStatus:
		"""Expose canonical status for API responses."""
		return self.status
