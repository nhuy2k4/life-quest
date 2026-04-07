import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin
from app.models.enums import ActivityLevel, sql_enum


class UserPreference(Base, UUIDMixin):
    """
    Sở thích người dùng — tạo rỗng khi register, điền khi onboarding.

    interests: ARRAY(int) — danh sách category_id đã chọn
    interest_weights: JSON — {"category_id": weight} tự cập nhật sau mỗi approve
    activity_level: 'low' | 'medium' | 'high'
    """

    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    interests: Mapped[list[int]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    interest_weights: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    activity_level: Mapped[Optional[ActivityLevel]] = mapped_column(
        sql_enum(ActivityLevel, name="activity_level_enum"),
        nullable=True,
    )
    location_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    notification_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="preference")

    def __repr__(self) -> str:
        return f"<UserPreference user={self.user_id}>"
