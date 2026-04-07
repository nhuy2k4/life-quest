"""Seed quest_categories for sample quests

Revision ID: 0006_seed_quest_categories
Revises: 0005_seed_sample_quests
Create Date: 2026-04-07 21:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0006_seed_quest_categories'
down_revision = '0005_seed_sample_quests'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    # Map quest title to category name
    mapping = [
        ("Uống 2 lít nước/ngày", "Sức khỏe"),
        ("Đi bộ 10.000 bước", "Thể thao"),
        ("Đọc sách 30 phút", "Học tập"),
        ("Tập thể dục 20 phút", "Thể thao"),
        ("Không dùng mạng xã hội 2 tiếng", "Giải trí"),
    ]
    for quest_title, category_name in mapping:
        quest_id = conn.execute(sa.text("SELECT id FROM quests WHERE title = :title"), {"title": quest_title}).scalar()
        category_id = conn.execute(sa.text("SELECT id FROM categories WHERE name = :name"), {"name": category_name}).scalar()
        if quest_id and category_id:
            conn.execute(
                sa.text("""
                    INSERT INTO quest_categories (quest_id, category_id)
                    VALUES (:quest_id, :category_id)
                    ON CONFLICT DO NOTHING
                """),
                {"quest_id": quest_id, "category_id": category_id}
            )

def downgrade():
    op.execute("DELETE FROM quest_categories WHERE quest_id IN (SELECT id FROM quests WHERE title IN ('Uống 2 lít nước/ngày', 'Đi bộ 10.000 bước', 'Đọc sách 30 phút', 'Tập thể dục 20 phút', 'Không dùng mạng xã hội 2 tiếng'))")
