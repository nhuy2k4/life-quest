"""Backfill quest_categories from quest data

Revision ID: 0033_backfill_quest_categories
Revises: 0032_add_user_quest_poi_id
Create Date: 2026-05-20 12:30:00.000000
"""

from __future__ import annotations

import json

from alembic import op
import sqlalchemy as sa

revision = "0033_backfill_quest_categories"
down_revision = "0032_add_user_quest_poi_id"
branch_labels = None
depends_on = None


CATEGORIES = [
    ("health", "Sức khỏe", "health"),
    ("study", "Học tập", "study"),
    ("sports", "Thể thao", "sports"),
    ("entertainment", "Giải trí", "entertainment"),
    ("food", "Food", "restaurant-outline"),
    ("travel", "Travel", "map-outline"),
    ("nature", "Nature", "leaf-outline"),
    ("photography", "Photography", "camera-outline"),
]

RULES = [
    ("food", {"coffee", "cafe", "drink", "beverage", "food", "meal", "dish", "restaurant", "market", "store"}),
    ("nature", {"park", "tree", "grass", "river", "water"}),
    ("travel", {"street", "road", "bridge", "building", "architecture"}),
    ("photography", {"photo", "camera", "shot", "view", "capture"}),
    ("health", {"nước", "uống"}),
    ("sports", {"walk", "steps", "bước", "tập", "thể", "dục"}),
    ("study", {"read", "book", "sách", "học"}),
    ("entertainment", {"social", "mạng", "giải", "trí"}),
]


def upgrade() -> None:
    conn = op.get_bind()
    _ensure_categories(conn)

    category_by_slug = {
        slug: category_id
        for slug, category_id in conn.execute(
            sa.text("SELECT slug, id FROM categories WHERE slug IS NOT NULL")
        ).all()
    }

    if not category_by_slug:
        category_by_slug = {
            _fallback_slug(name): category_id
            for name, category_id in conn.execute(
                sa.text("SELECT name, id FROM categories")
            ).all()
        }

    quests = conn.execute(
        sa.text("SELECT id, title, description, labels FROM quests")
    ).mappings().all()

    for quest in quests:
        slugs = _category_slugs_for_quest(
            title=quest["title"],
            description=quest["description"],
            labels=quest["labels"],
        )

        for slug in slugs:
            category_id = category_by_slug.get(slug)
            if category_id is None:
                continue

            conn.execute(
                sa.text(
                    """
                    INSERT INTO quest_categories (quest_id, category_id)
                    VALUES (:quest_id, :category_id)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {
                    "quest_id": quest["id"],
                    "category_id": category_id,
                },
            )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM quest_categories
        WHERE quest_id IN (
            SELECT id FROM quests
            WHERE labels IS NOT NULL
               OR title IN (
                    'Coffee hunt',
                    'Street view',
                    'Park moment',
                    'Bridge view',
                    'Market visit',
                    'Food stop',
                    'Restaurant hunt',
                    'Drink moment',
                    'Building shot',
                    'River view'
               )
        )
        """
    )


def _ensure_categories(conn) -> None:
    for slug, name, icon in CATEGORIES:
        conn.execute(
            sa.text(
                """
                INSERT INTO categories (slug, name, icon)
                SELECT
                    CAST(:slug AS VARCHAR),
                    CAST(:name AS VARCHAR),
                    CAST(:icon AS VARCHAR)
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM categories
                    WHERE slug = CAST(:slug AS VARCHAR)
                       OR name = CAST(:name AS VARCHAR)
                )
                """
            ),
            {
                "slug": slug,
                "name": name,
                "icon": icon,
            },
        )


def _category_slugs_for_quest(
    *,
    title: str | None,
    description: str | None,
    labels,
) -> set[str]:
    tokens = set(_labels_to_list(labels))
    haystack = " ".join([title or "", description or "", " ".join(tokens)]).lower()

    slugs = {
        slug
        for slug, keywords in RULES
        if any(keyword.lower() in haystack for keyword in keywords)
    }

    if not slugs:
        slugs.add("photography")

    return slugs


def _labels_to_list(labels) -> list[str]:
    if labels is None:
        return []

    if isinstance(labels, list):
        return [str(item).lower() for item in labels if item]

    if isinstance(labels, str):
        try:
            parsed = json.loads(labels)
        except json.JSONDecodeError:
            return [labels.lower()]

        if isinstance(parsed, list):
            return [str(item).lower() for item in parsed if item]

    return []


def _fallback_slug(name: str) -> str:
    normalized = name.strip().lower()

    mapping = {
        "sức khỏe": "health",
        "học tập": "study",
        "thể thao": "sports",
        "giải trí": "entertainment",
    }

    return mapping.get(normalized, normalized.replace(" ", "-"))