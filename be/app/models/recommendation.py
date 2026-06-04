import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin

if TYPE_CHECKING:
    from app.models.social import Post
    from app.models.quest import Quest
    from app.models.user import User


class RecommendationLog(Base, UUIDMixin):
    __tablename__ = "recommendation_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quest_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("quests.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    post_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    event: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    algorithm_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v2_mvp")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User")
    quest: Mapped["Quest | None"] = relationship("Quest")
    post: Mapped["Post | None"] = relationship("Post")


