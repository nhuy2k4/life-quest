import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin
from app.models.enums import UserQuestStatus, sql_enum

if TYPE_CHECKING:
	from app.models.quest import Quest
	from app.models.submission import Submission
	from app.models.user import User


STARTED_STATUSES = {UserQuestStatus.STARTED}
TERMINAL_STATUSES = {UserQuestStatus.APPROVED, UserQuestStatus.REJECTED}


class UserQuest(Base, UUIDMixin):
	__tablename__ = "user_quests"

	user_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		nullable=False,
	)
	quest_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("quests.id", ondelete="CASCADE"),
		nullable=False,
	)
	status: Mapped[UserQuestStatus] = mapped_column(
		sql_enum(UserQuestStatus, name="user_quest_status_enum"),
		nullable=False,
		default=UserQuestStatus.STARTED,
	)
	started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

	user: Mapped["User"] = relationship("User")
	quest: Mapped["Quest"] = relationship("Quest", back_populates="user_quests")
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
