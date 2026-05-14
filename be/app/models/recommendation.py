import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.quest import Quest
    from app.models.user import User


class RecommendationLog(Base, UUIDMixin):
    __tablename__ = "recommendation_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quest_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    algorithm_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v2_mvp")
    reasons: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    score_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    features_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    rule_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ml_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User")
    quest: Mapped["Quest"] = relationship("Quest")


class QuestStatsDaily(Base, UUIDMixin):
    __tablename__ = "quest_stats_daily"

    quest_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stat_date: Mapped[date] = mapped_column(Date, nullable=False)
    shown: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clicked: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ignored: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_completion_time_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    popularity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    quest: Mapped["Quest"] = relationship("Quest")


class UserQuestStats(Base, UUIDMixin):
    __tablename__ = "user_quest_stats"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    abandoned_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_completion_time_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    completion_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    last_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User")


class UserAiStats(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_ai_stats"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    vision_success_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    poi_success_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recent_fail_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["User"] = relationship("User")


class TrendingScore(Base, UUIDMixin):
    __tablename__ = "trending_scores"

    quest_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    window: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    quest: Mapped["Quest"] = relationship("Quest")
