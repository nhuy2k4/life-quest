import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin

if TYPE_CHECKING:
	from app.models.quest import Quest
	from app.models.submission import Submission
	from app.models.user import User


class UserQuestStatus:
	"""Canonical quest statuses used by API/service layer."""

	NOT_STARTED = "not_started"
	STARTED = "started"
	SUBMITTED = "submitted"
	APPROVED = "approved"
	REJECTED = "rejected"

	# Backward-compat value from initial migration.
	LEGACY_IN_PROGRESS = "in_progress"

	STARTED_STATUSES = {STARTED, LEGACY_IN_PROGRESS}
	TERMINAL_STATUSES = {APPROVED, REJECTED}


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
	status: Mapped[str] = mapped_column(String(20), nullable=False, default=UserQuestStatus.LEGACY_IN_PROGRESS)
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
	def normalized_status(self) -> str:
		"""Map legacy status to canonical status for API responses."""
		if self.status == UserQuestStatus.LEGACY_IN_PROGRESS:
			return UserQuestStatus.STARTED
		return self.status
