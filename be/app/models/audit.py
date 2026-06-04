import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDMixin

if TYPE_CHECKING:
    from app.models.submission import Submission
    from app.models.user import User


class AiDetectionLog(Base, UUIDMixin):
    __tablename__ = "ai_detection_logs"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    labels: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_stats: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    submission: Mapped["Submission"] = relationship("Submission", back_populates="ai_logs")


class AuditLog(Base, UUIDMixin):
    __tablename__ = "audit_logs"

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    meta: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    actor: Mapped["User | None"] = relationship("User", back_populates="audit_logs")
