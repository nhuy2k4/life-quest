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
    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"


class ActivityLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class XpSource(StrEnum):
    QUEST_APPROVED = "quest_approved"


def sql_enum(enum_cls: type[StrEnum], name: str) -> SQLEnum:
    """Create SQLAlchemy Enum that stores enum .value (lowercase tokens) in DB."""
    return SQLEnum(
        enum_cls,
        name=name,
        values_callable=lambda cls: [item.value for item in cls],
        validate_strings=True,
    )