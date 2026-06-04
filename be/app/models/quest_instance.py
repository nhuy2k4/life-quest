import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QuestInstance(Base):
    """
    Quest instance gắn theo user + POI.

    Tối ưu bằng cách chỉ lưu khóa ngoại (quest_id, user_id, poi_id)
    thay vì sao chép tên/metadata.
    """

    __tablename__ = "quest_instances"

    quest_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quests.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    poi_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pois.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    quest: Mapped["Quest"] = relationship("Quest")
    user: Mapped["User"] = relationship("User")
    poi: Mapped["Poi"] = relationship("Poi")
