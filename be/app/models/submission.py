import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin
from app.models.enums import SubmissionStatus, sql_enum

if TYPE_CHECKING:
	from app.models.audit import AiDetectionLog
	from app.models.user_quest import UserQuest
	from app.models.social import Post
	from app.models.poi import Poi


class Submission(Base, UUIDMixin):
	__tablename__ = "submissions"

	user_quest_id: Mapped[uuid.UUID] = mapped_column(
		ForeignKey("user_quests.id", ondelete="CASCADE"),
		nullable=False,
		unique=True,
	)
	image_url: Mapped[str] = mapped_column(String(500), nullable=False)
	cloudinary_public_id: Mapped[str] = mapped_column(String(255), nullable=False)
	file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
	retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
	vision_labels: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
	vision_raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)
	ai_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
	lat: Mapped[float | None] = mapped_column(Float, nullable=True)
	lng: Mapped[float | None] = mapped_column(Float, nullable=True)
	location_accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
	location_captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
	poi_id: Mapped[uuid.UUID | None] = mapped_column(
		ForeignKey("pois.id", ondelete="SET NULL"),
		nullable=True,
	)
	poi_distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
	cheat_flags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
	ai_score: Mapped[float | None] = mapped_column(Float, nullable=True)
	status: Mapped[SubmissionStatus] = mapped_column(
		sql_enum(SubmissionStatus, name="submission_status_enum"),
		nullable=False,
		default=SubmissionStatus.PENDING,
		index=True,
	)
	is_suspicious: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
	rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

	user_quest: Mapped["UserQuest"] = relationship("UserQuest", back_populates="submission")
	post: Mapped["Post | None"] = relationship("Post", back_populates="submission")
	poi: Mapped["Poi | None"] = relationship("Poi", back_populates="submissions")
	ai_logs: Mapped[list["AiDetectionLog"]] = relationship(
		"AiDetectionLog",
		back_populates="submission",
		cascade="all, delete-orphan",
	)
