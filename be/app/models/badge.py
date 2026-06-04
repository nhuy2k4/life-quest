import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin

if TYPE_CHECKING:
	from app.models.user import User


class Badge(Base, UUIDMixin):
	__tablename__ = "badges"

	name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
	description: Mapped[str] = mapped_column(Text, nullable=False, default="")
	icon_url: Mapped[str] = mapped_column(String(255), nullable=False, default="")
	rarity: Mapped[str] = mapped_column(String(30), nullable=False, default="common")
	category: Mapped[str] = mapped_column(String(50), nullable=False, default="general")
	criteria: Mapped[dict] = mapped_column(JSON, nullable=False)
	is_hidden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
	is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
	sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		nullable=False,
	)
	updated_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)

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
