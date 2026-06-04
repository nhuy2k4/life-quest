"""Seed photo object quests

Revision ID: 0045_seed_photo_object_quests
Revises: 0044_add_poi_id_to_posts
Create Date: 2026-05-26
"""

from __future__ import annotations

import json
from datetime import datetime
from uuid import UUID

from alembic import op
import sqlalchemy as sa


revision = "0045_seed_photo_object_quests"
down_revision = "0044_add_poi_id_to_posts"
branch_labels = None
depends_on = None


CATEGORIES = [
    ("workspace", "Workspace", "briefcase-outline"),
    ("pets", "Pets", "paw-outline"),
]


QUESTS = [
    {
        "id": UUID("39f6628f-6e3d-4cd0-a663-c6ad3e61b979"),
        "title": "Chụp cái bàn",
        "description": "Chụp một cái bàn rõ ràng trong khung hình.",
        "labels": ["table", "desk"],
        "label_rules": {"table": 0.55, "desk": 0.55},
        "xp_reward": 40,
        "difficulty": "easy",
        "categories": ["workspace", "photography"],
    },
    {
        "id": UUID("26bf5917-413d-4456-8b60-3da04fa264d4"),
        "title": "Chụp bút",
        "description": "Chụp một cây bút hoặc dụng cụ viết.",
        "labels": ["pen", "pencil"],
        "label_rules": {"pen": 0.5, "pencil": 0.5},
        "xp_reward": 35,
        "difficulty": "easy",
        "categories": ["workspace", "photography"],
    },
    {
        "id": UUID("362b5353-41f4-463f-9b6d-11d131950ead"),
        "title": "Chụp laptop",
        "description": "Chụp một chiếc laptop hoặc máy tính xách tay.",
        "labels": ["laptop", "computer", "personal computer"],
        "label_rules": {"laptop": 0.55, "computer": 0.6, "personal computer": 0.55},
        "xp_reward": 45,
        "difficulty": "easy",
        "categories": ["workspace", "photography"],
    },
    {
        "id": UUID("5b33e386-726f-4b02-8d32-1d96edfc5cf9"),
        "title": "Chụp cái cặp",
        "description": "Chụp một cái cặp, túi xách hoặc ba lô.",
        "labels": ["bag", "backpack", "handbag"],
        "label_rules": {"bag": 0.5, "backpack": 0.5, "handbag": 0.5},
        "xp_reward": 40,
        "difficulty": "easy",
        "categories": ["workspace", "photography"],
    },
    {
        "id": UUID("b99eb8ce-8b14-4cb8-81d5-b5d71e3ac8df"),
        "title": "Chụp ly nước",
        "description": "Chụp một ly nước, chai nước hoặc đồ uống.",
        "labels": ["drinkware", "cup", "water bottle", "drink", "beverage"],
        "label_rules": {"drinkware": 0.5, "cup": 0.5, "water bottle": 0.5, "drink": 0.5},
        "xp_reward": 40,
        "difficulty": "easy",
        "categories": ["food", "photography"],
    },
    {
        "id": UUID("a65f6494-33a0-413b-9f67-c89306f2b08d"),
        "title": "Chụp với con người",
        "description": "Chụp ảnh có ít nhất một con người xuất hiện rõ ràng.",
        "labels": ["person", "people", "human"],
        "label_rules": {"person": 0.55, "people": 0.55, "human": 0.55},
        "xp_reward": 55,
        "difficulty": "easy",
        "categories": ["community", "photography"],
    },
    {
        "id": UUID("d5a5923a-942a-43ec-90e1-859bda8833c0"),
        "title": "Chụp với con chó",
        "description": "Chụp ảnh có một con chó xuất hiện rõ ràng.",
        "labels": ["dog"],
        "label_rules": {"dog": 0.55},
        "xp_reward": 55,
        "difficulty": "easy",
        "categories": ["pets", "photography"],
    },
    {
        "id": UUID("d9bfde7a-fd9f-4562-b64b-3f7b4bec7fd5"),
        "title": "Chụp với con mèo",
        "description": "Chụp ảnh có một con mèo xuất hiện rõ ràng.",
        "labels": ["cat"],
        "label_rules": {"cat": 0.55},
        "xp_reward": 55,
        "difficulty": "easy",
        "categories": ["pets", "photography"],
    },
    {
        "id": UUID("96fe0c18-7136-4a36-b6e1-a64710e77532"),
        "title": "Chụp với cái ghế",
        "description": "Chụp một cái ghế rõ ràng trong khung hình.",
        "labels": ["chair"],
        "label_rules": {"chair": 0.55},
        "xp_reward": 40,
        "difficulty": "easy",
        "categories": ["workspace", "photography"],
    },
]


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.utcnow()

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
            {"slug": slug, "name": name, "icon": icon},
        )

    for quest in QUESTS:
        conn.execute(
            sa.text(
                """
                INSERT INTO quests (
                    id,
                    title,
                    description,
                    xp_reward,
                    difficulty,
                    approval_rate,
                    time_limit_hours,
                    location_required,
                    is_active,
                    template,
                    labels,
                    label_rules,
                    min_confidence,
                    created_at,
                    updated_at
                )
                SELECT
                    CAST(:id AS UUID),
                    CAST(:title AS VARCHAR),
                    CAST(:description AS TEXT),
                    CAST(:xp_reward AS INTEGER),
                    CAST(:difficulty AS quest_difficulty_enum),
                    1.0,
                    NULL,
                    FALSE,
                    TRUE,
                    CAST(:template AS VARCHAR),
                    CAST(:labels AS JSON),
                    CAST(:label_rules AS JSON),
                    0.5,
                    :created_at,
                    :updated_at
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM quests
                    WHERE title = CAST(:title AS VARCHAR)
                )
                """
            ),
            {
                "id": str(quest["id"]),
                "title": quest["title"],
                "description": quest["description"],
                "xp_reward": quest["xp_reward"],
                "difficulty": quest["difficulty"],
                "template": quest["title"],
                "labels": json.dumps(quest["labels"]),
                "label_rules": json.dumps(quest["label_rules"]),
                "created_at": now,
                "updated_at": now,
            },
        )

        for slug in quest["categories"]:
            conn.execute(
                sa.text(
                    """
                    INSERT INTO quest_categories (quest_id, category_id)
                    SELECT q.id, c.id
                    FROM quests q
                    JOIN categories c ON c.slug = CAST(:slug AS VARCHAR)
                    WHERE q.title = CAST(:title AS VARCHAR)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"title": quest["title"], "slug": slug},
            )


def downgrade() -> None:
    conn = op.get_bind()
    titles = [quest["title"] for quest in QUESTS]
    conn.execute(
        sa.text(
            """
            DELETE FROM quest_categories
            WHERE quest_id IN (
                SELECT id FROM quests WHERE title IN :titles
            )
            """
        ).bindparams(sa.bindparam("titles", expanding=True)),
        {"titles": titles},
    )
    conn.execute(
        sa.text("DELETE FROM quests WHERE title IN :titles").bindparams(
            sa.bindparam("titles", expanding=True)
        ),
        {"titles": titles},
    )
    op.execute(
        """
        DELETE FROM categories
        WHERE slug IN ('workspace', 'pets')
          AND id NOT IN (SELECT category_id FROM quest_categories)
        """
    )
