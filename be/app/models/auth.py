import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin


class Level(Base):
    """
    Bảng tĩnh 10 dòng — ngưỡng XP từng level.
    Seed trong migration, không thay đổi lúc runtime.
    """

    __tablename__ = "levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    required_xp: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationship ngược về Users
    users: Mapped[list["User"]] = relationship("User", back_populates="level")

    def __repr__(self) -> str:
        return f"<Level {self.id}: {self.name} ({self.required_xp} XP)>"


class RefreshToken(Base, UUIDMixin):
    """
    Lưu refresh token đã phát.
    - is_revoked: thu hồi ngay khi logout/đổi role (không cần chờ hết hạn)
    - expires_at: cron maintenance_tasks dọn hàng ngày
    - token_hash: SHA256 của raw token — không bao giờ lưu plain text
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    @property
    def is_valid(self) -> bool:
        """Kiểm tra token còn hợp lệ (chưa bị revoke và chưa hết hạn)."""
        expires_at = self.expires_at

        # Một số DB/driver có thể trả về datetime naive dù cột khai báo timezone=True.
        # Chuẩn hóa về UTC-aware để tránh TypeError khi so sánh naive vs aware.
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        return not self.is_revoked and expires_at > datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return f"<RefreshToken user={self.user_id} revoked={self.is_revoked}>"
