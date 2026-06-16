from enum import StrEnum

from sqlalchemy import Enum as SQLEnum


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class AuthProvider(StrEnum):
    LOCAL = "local"
    GOOGLE = "google"


class QuestDifficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class UserQuestStatus(StrEnum):
    NOT_STARTED = "not_started"
    STARTED = "started"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class SubmissionStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"


class EventStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    ENDED = "ended"


class ActivityLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class XpSource(StrEnum):
    QUEST_APPROVED = "quest_approved"
    CONSOLATION = "consolation"
    ADMIN_ADJUST = "admin_adjust"
    EVENT_REWARD = "event_reward"


class PostVisibility(StrEnum):
    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"


def sql_enum(enum_cls: type[StrEnum], name: str) -> SQLEnum:
    """Create SQLAlchemy Enum that stores enum .value (lowercase tokens) in DB."""
    return SQLEnum(
        enum_cls,
        name=name,
        values_callable=lambda cls: [item.value for item in cls],
        validate_strings=True,
    )