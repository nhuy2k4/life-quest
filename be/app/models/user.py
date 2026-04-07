from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.models.enums import AuthProvider, UserRole, sql_enum

if TYPE_CHECKING:
    from app.models.auth import Level, RefreshToken
    from app.models.user_preference import UserPreference


class User(Base, UUIDMixin, TimestampMixin):
    """
    Tài khoản người dùng — trung tâm của hệ thống.

    Roles: 'user' | 'admin'
    Status: is_banned — Khóa tài khoản
    Onboarding: onboarding_completed — chặn quest endpoints nếu False
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[AuthProvider] = mapped_column(
        sql_enum(AuthProvider, name="auth_provider_enum"),
        nullable=False,
        default=AuthProvider.LOCAL,
    )
    provider_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # ── Level & Gamification ──────────────────────────────────────────────────
    level_id: Mapped[int] = mapped_column(
        ForeignKey("levels.id"),
        default=1,
        nullable=False,
    )
    xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)

    # ── Access Control ────────────────────────────────────────────────────────
    role: Mapped[UserRole] = mapped_column(
        sql_enum(UserRole, name="user_role_enum"),
        nullable=False,
        default=UserRole.USER,
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    level: Mapped["Level"] = relationship("Level", back_populates="users")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    preference: Mapped["UserPreference"] = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
