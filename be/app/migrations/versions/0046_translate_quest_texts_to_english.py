"""Translate quest titles/descriptions/templates to English

Revision ID: 0046_translate_quest_texts_to_english
Revises: 0045_seed_photo_object_quests
Create Date: 2026-05-28
"""

from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = "0046_translate_quest_texts_to_english"
down_revision = "0045_seed_photo_object_quests"
branch_labels = None
depends_on = None


QUEST_UPDATES = [
    {
        "id": "26bf5917-413d-4456-8b60-3da04fa264d4",
        "title": "Pen shot",
        "description": "Take a photo of a pen or writing tool.",
        "template": "Take a photo of a {label}",
    },
    {
        "id": "362b5353-41f4-463f-9b6d-11d131950ead",
        "title": "Laptop shot",
        "description": "Take a photo of a laptop or portable computer.",
        "template": "Take a photo of a {label}",
    },
    {
        "id": "39f6628f-6e3d-4cd0-a663-c6ad3e61b979",
        "title": "Table shot",
        "description": "Capture a table clearly in the frame.",
        "template": "Take a photo of a {label}",
    },
    {
        "id": "5b33e386-726f-4b02-8d32-1d96edfc5cf9",
        "title": "Bag shot",
        "description": "Take a photo of a bag, handbag, or backpack.",
        "template": "Take a photo of a {label}",
    },
    {
        "id": "96fe0c18-7136-4a36-b6e1-a64710e77532",
        "title": "Chair shot",
        "description": "Capture a chair clearly in the frame.",
        "template": "Take a photo of a {label}",
    },
    {
        "id": "a65f6494-33a0-413b-9f67-c89306f2b08d",
        "title": "People shot",
        "description": "Take a photo with at least one person clearly visible.",
        "template": "Capture a {label} in the frame",
    },
    {
        "id": "b99eb8ce-8b14-4cb8-81d5-b5d71e3ac8df",
        "title": "Drinkware shot",
        "description": "Take a photo of a cup, water bottle, or drink.",
        "template": "Take a photo of a {label}",
    },
    {
        "id": "d5a5923a-942a-43ec-90e1-859bda8833c0",
        "title": "Dog shot",
        "description": "Take a photo with a dog clearly visible.",
        "template": "Capture a {label} in the frame",
    },
    {
        "id": "d9bfde7a-fd9f-4562-b64b-3f7b4bec7fd5",
        "title": "Cat shot",
        "description": "Take a photo with a cat clearly visible.",
        "template": "Capture a {label} in the frame",
    },
]


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.utcnow()

    for quest in QUEST_UPDATES:
        conn.execute(
            sa.text(
                """
                UPDATE quests
                SET
                    title = CAST(:title AS VARCHAR),
                    description = CAST(:description AS TEXT),
                    template = CAST(:template AS VARCHAR),
                    updated_at = :updated_at
                WHERE id = CAST(:id AS UUID)
                """
            ),
            {
                "id": quest["id"],
                "title": quest["title"],
                "description": quest["description"],
                "template": quest["template"],
                "updated_at": now,
            },
        )


def downgrade() -> None:
    pass
