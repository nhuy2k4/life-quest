import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin

if TYPE_CHECKING:
	from app.models.user import User


class Badge(Base, UUIDMixin):
	__tablename__ = "badges"

	name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
	icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
	criteria: Mapped[dict] = mapped_column(JSON, nullable=False)

	user_badges: Mapped[list["UserBadge"]] = relationship(
		"UserBadge",
		back_populates="badge",
		cascade="all, delete-orphan",
	)


class UserBadge(Base, UUIDMixin):
	__tablename__ = "user_badges"

	user_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		nullable=False,
		index=True,
	)
	badge_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("badges.id", ondelete="CASCADE"),
		nullable=False,
	)
	earned_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		nullable=False,
	)

	user: Mapped["User"] = relationship("User", back_populates="badges")
	badge: Mapped["Badge"] = relationship("Badge", back_populates="user_badges")
