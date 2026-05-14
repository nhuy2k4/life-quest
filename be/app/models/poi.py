import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.quest import Quest
    from app.models.submission import Submission


class Poi(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "pois"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_pois_source_external_id"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    poi_type: Mapped[str] = mapped_column(String(50), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    radius_m: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    external_id: Mapped[str] = mapped_column(String(64), nullable=False)
    external_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    quests: Mapped[list["Quest"]] = relationship("Quest", back_populates="poi")
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="poi")
