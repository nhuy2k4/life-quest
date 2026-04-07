import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin
from app.models.enums import XpSource, sql_enum

if TYPE_CHECKING:
	from app.models.submission import Submission
	from app.models.user import User


class XpTransaction(Base, UUIDMixin):
	__tablename__ = "xp_transactions"

	user_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		nullable=False,
		index=True,
	)
	submission_id: Mapped[uuid.UUID | None] = mapped_column(
		ForeignKey("submissions.id"),
		nullable=True,
		index=True,
	)
	amount: Mapped[int] = mapped_column(Integer, nullable=False)
	source: Mapped[XpSource] = mapped_column(
		sql_enum(XpSource, name="xp_source_enum"),
		nullable=False,
		default=XpSource.QUEST_APPROVED,
	)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

	user: Mapped["User"] = relationship("User")
	submission: Mapped["Submission | None"] = relationship("Submission")
