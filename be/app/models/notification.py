import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin

if TYPE_CHECKING:
	from app.models.user import User


class Notification(Base, UUIDMixin):
	__tablename__ = "notifications"

	user_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		nullable=False,
		index=True,
	)
	type: Mapped[str] = mapped_column(String(50), nullable=False)
	data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
	is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		nullable=False,
	)

	user: Mapped["User"] = relationship("User", back_populates="notifications")


class UserPushToken(Base, UUIDMixin):
	__tablename__ = "user_push_tokens"
	__table_args__ = (
		UniqueConstraint("token", name="uq_user_push_tokens_token"),
	)

	user_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("users.id", ondelete="CASCADE"),
		nullable=False,
		index=True,
	)
	token: Mapped[str] = mapped_column(String(255), nullable=False)
	provider: Mapped[str] = mapped_column(String(30), nullable=False, default="expo")
	platform: Mapped[str | None] = mapped_column(String(30), nullable=True)
	is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
	created_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		nullable=False,
	)
	last_seen_at: Mapped[datetime] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
		nullable=False,
	)
