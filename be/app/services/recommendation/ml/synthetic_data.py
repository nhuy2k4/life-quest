from __future__ import annotations

import random
import uuid
from typing import Any

import pandas as pd

from app.services.recommendation.ml.feature_builder import build_feature_snapshot


def generate_fake_users(count: int, seed: int = 42) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    users: list[dict[str, Any]] = []
    for _ in range(count):
        completion_rate = rng.uniform(0.2, 0.9)
        activity_level = rng.choice(["low", "medium", "high"])
        streak_days = rng.randint(0, 20)
        avg_difficulty_pref = rng.uniform(0.2, 1.0)
        users.append(
            {
                "user_id": uuid.uuid4(),
                "completion_rate": completion_rate,
                "activity_level": activity_level,
                "streak_days": streak_days,
                "avg_difficulty_pref": avg_difficulty_pref,
            }
        )
    return users


def generate_fake_quests(count: int, seed: int = 42) -> list[dict[str, Any]]:
    rng = random.Random(seed + 17)
    quests: list[dict[str, Any]] = []
    for _ in range(count):
        quests.append(
            {
                "quest_id": uuid.uuid4(),
                "difficulty": rng.choice(["easy", "medium", "hard"]),
                "popularity": rng.uniform(0.1, 1.0),
                "freshness_score": rng.uniform(0.0, 1.0),
                "ai_required_score": rng.choice([0.0, 0.3, 0.6, 1.0]),
            }
        )
    return quests


def _simulate_label(
    user: dict[str, Any],
    quest: dict[str, Any],
    interaction: dict[str, Any],
    rng: random.Random,
) -> int:
    user_skill = (user.get("completion_rate", 0.5) + user.get("avg_difficulty_pref", 0.5)) / 2.0
    difficulty = quest.get("difficulty", 0.5)
    difficulty_gap = max(min(user_skill - difficulty, 1.0), -1.0)
    base = 0.5 + 0.4 * difficulty_gap
    base += 0.05 * min(interaction.get("friend_completed_count", 0) / 5.0, 1.0)
    base -= 0.05 * min(interaction.get("retry_count", 0) / 5.0, 1.0)
    noise = rng.uniform(-0.1, 0.1)
    prob = max(min(base + noise, 0.95), 0.05)
    return 1 if rng.random() < prob else 0


def _rebalance_labels(labels: list[int], rng: random.Random, target_rate: float = 0.5) -> list[int]:
    if not labels:
        return labels
    positive_rate = sum(labels) / len(labels)
    if 0.35 <= positive_rate <= 0.65:
        return labels

    labels = labels[:]
    desired_positives = int(len(labels) * target_rate)
    current_positives = sum(labels)
    if current_positives < desired_positives:
        zero_indices = [i for i, label in enumerate(labels) if label == 0]
        rng.shuffle(zero_indices)
        for i in zero_indices[: desired_positives - current_positives]:
            labels[i] = 1
    else:
        one_indices = [i for i, label in enumerate(labels) if label == 1]
        rng.shuffle(one_indices)
        for i in one_indices[: current_positives - desired_positives]:
            labels[i] = 0
    return labels


def generate_synthetic_dataset(
    users: list[dict[str, Any]],
    quests: list[dict[str, Any]],
    samples_per_user: int = 40,
    seed: int = 42,
) -> pd.DataFrame:
    rng = random.Random(seed)
    rows: list[dict[str, Any]] = []
    labels: list[int] = []

    for user in users:
        for _ in range(samples_per_user):
            quest = rng.choice(quests)
            interaction = {
                "retry_count": rng.randint(0, 5),
                "friend_completed_count": rng.randint(0, 6),
            }
            feature_snapshot = build_feature_snapshot(
                {
                    "completion_rate": user.get("completion_rate"),
                    "activity_level": user.get("activity_level"),
                    "streak_days": user.get("streak_days"),
                    "avg_difficulty_pref": user.get("avg_difficulty_pref"),
                },
                {
                    "difficulty": quest.get("difficulty"),
                    "popularity": quest.get("popularity"),
                    "freshness_score": quest.get("freshness_score"),
                    "ai_required_score": quest.get("ai_required_score"),
                },
                interaction,
            )
            label = _simulate_label(user, feature_snapshot, interaction, rng)
            labels.append(label)
            rows.append(
                {
                    "user_id": user.get("user_id"),
                    "quest_id": quest.get("quest_id"),
                    **feature_snapshot,
                    "label": label,
                }
            )

    labels = _rebalance_labels(labels, rng)
    for index, label in enumerate(labels):
        rows[index]["label"] = label

    return pd.DataFrame(rows)


def save_dataset(df: pd.DataFrame, csv_path: str) -> None:
    df.to_csv(csv_path, index=False)
