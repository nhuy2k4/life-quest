from __future__ import annotations

from typing import Any

try:
    from app.models.enums import ActivityLevel, QuestDifficulty
except Exception:  # pragma: no cover - optional import for training
    ActivityLevel = None
    QuestDifficulty = None

FEATURE_ORDER: list[str] = [
    "completion_rate",
    "activity_level",
    "streak_days",
    "avg_difficulty_pref",
    "difficulty",
    "popularity",
    "freshness_score",
    "ai_required_score",
    "retry_count",
    "friend_completed_count",
]

ACTIVITY_LEVEL_MAP = {
    "low": 0.2,
    "medium": 0.6,
    "high": 1.0,
}

DIFFICULTY_MAP = {
    "easy": 0.2,
    "medium": 0.6,
    "hard": 1.0,
}


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def encode_activity_level(value: Any) -> float:
    if ActivityLevel and isinstance(value, ActivityLevel):
        return ACTIVITY_LEVEL_MAP.get(value.value, 0.5)
    if hasattr(value, "value"):
        return ACTIVITY_LEVEL_MAP.get(str(value.value).lower(), 0.5)
    if isinstance(value, str):
        return ACTIVITY_LEVEL_MAP.get(value.lower(), 0.5)
    return _coerce_float(value, 0.5)


def encode_difficulty(value: Any) -> float:
    if QuestDifficulty and isinstance(value, QuestDifficulty):
        return DIFFICULTY_MAP.get(value.value, 0.5)
    if hasattr(value, "value"):
        return DIFFICULTY_MAP.get(str(value.value).lower(), 0.5)
    if isinstance(value, str):
        return DIFFICULTY_MAP.get(value.lower(), 0.5)
    return _coerce_float(value, 0.5)


def build_feature_snapshot(
    user_features: dict[str, Any],
    quest_features: dict[str, Any],
    interaction_features: dict[str, Any],
) -> dict[str, float]:
    return {
        "completion_rate": _coerce_float(user_features.get("completion_rate"), 0.0),
        "activity_level": encode_activity_level(user_features.get("activity_level")),
        "streak_days": _coerce_float(user_features.get("streak_days"), 0.0),
        "avg_difficulty_pref": _coerce_float(user_features.get("avg_difficulty_pref"), 0.5),
        "difficulty": encode_difficulty(quest_features.get("difficulty")),
        "popularity": _coerce_float(quest_features.get("popularity"), 0.0),
        "freshness_score": _coerce_float(quest_features.get("freshness_score"), 0.0),
        "ai_required_score": _coerce_float(quest_features.get("ai_required_score"), 0.0),
        "retry_count": _coerce_float(interaction_features.get("retry_count"), 0.0),
        "friend_completed_count": _coerce_float(interaction_features.get("friend_completed_count"), 0.0),
    }


def vectorize_features(
    feature_snapshot: dict[str, float],
    feature_order: list[str] | None = None,
) -> list[float]:
    order = feature_order or FEATURE_ORDER
    return [_coerce_float(feature_snapshot.get(name, 0.0), 0.0) for name in order]


def get_feature_schema() -> list[str]:
    return list(FEATURE_ORDER)
