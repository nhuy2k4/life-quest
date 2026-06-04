"""Seed default badges

Revision ID: 0039_seed_badges
Revises: 0038_drop_reco_log_reasons
Create Date: 2026-05-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "0039_seed_badges"
down_revision = "0038_drop_reco_log_reasons"
branch_labels = None
depends_on = None


BADGES = [
	{
		"id": "11111111-1111-4111-8111-111111111111",
		"name": "First Quest",
		"icon": "flag-outline",
		"description": "Complete your first quest.",
		"icon_url": "flag-outline",
		"rarity": "common",
		"category": "quests",
		"is_hidden": False,
		"is_active": True,
		"sort_order": 10,
		"criteria": {"type": "quests_completed", "count": 1},
	},
	{
		"id": "22222222-2222-4222-8222-222222222222",
		"name": "Quest Rookie",
		"icon": "walk-outline",
		"description": "Complete 5 quests.",
		"icon_url": "walk-outline",
		"rarity": "common",
		"category": "quests",
		"is_hidden": False,
		"is_active": True,
		"sort_order": 20,
		"criteria": {"type": "quests_completed", "count": 5},
	},
	{
		"id": "33333333-3333-4333-8333-333333333333",
		"name": "Quest Pro",
		"icon": "trophy-outline",
		"description": "Complete 20 quests.",
		"icon_url": "trophy-outline",
		"rarity": "rare",
		"category": "quests",
		"is_hidden": False,
		"is_active": True,
		"sort_order": 30,
		"criteria": {"type": "quests_completed", "count": 20},
	},
	{
		"id": "44444444-4444-4444-8444-444444444444",
		"name": "Century Explorer",
		"icon": "ribbon-outline",
		"description": "Complete 100 quests.",
		"icon_url": "ribbon-outline",
		"rarity": "legendary",
		"category": "quests",
		"is_hidden": True,
		"is_active": True,
		"sort_order": 40,
		"criteria": {"type": "quests_completed", "count": 100},
	},
	{
		"id": "55555555-5555-4555-8555-555555555555",
		"name": "First Post",
		"icon": "image-outline",
		"description": "Share your first post.",
		"icon_url": "image-outline",
		"rarity": "common",
		"category": "social",
		"is_hidden": False,
		"is_active": True,
		"sort_order": 50,
		"criteria": {"type": "posts_created", "count": 1},
	},
	{
		"id": "66666666-6666-4666-8666-666666666666",
		"name": "Social Spark",
		"icon": "chatbubbles-outline",
		"description": "Write 10 comments.",
		"icon_url": "chatbubbles-outline",
		"rarity": "common",
		"category": "social",
		"is_hidden": False,
		"is_active": True,
		"sort_order": 60,
		"criteria": {"type": "comments_created", "count": 10},
	},
	{
		"id": "77777777-7777-4777-8777-777777777777",
		"name": "Community Favorite",
		"icon": "heart-outline",
		"description": "Receive 25 likes across your posts.",
		"icon_url": "heart-outline",
		"rarity": "rare",
		"category": "social",
		"is_hidden": False,
		"is_active": True,
		"sort_order": 70,
		"criteria": {"type": "likes_received", "count": 25},
	},
	{
		"id": "88888888-8888-4888-8888-888888888888",
		"name": "Streak Starter",
		"icon": "flame-outline",
		"description": "Reach a 3-day streak.",
		"icon_url": "flame-outline",
		"rarity": "common",
		"category": "streak",
		"is_hidden": False,
		"is_active": True,
		"sort_order": 80,
		"criteria": {"type": "streak_days", "count": 3},
	},
	{
		"id": "99999999-9999-4999-8999-999999999999",
		"name": "On Fire",
		"icon": "flame",
		"description": "Reach a 7-day streak.",
		"icon_url": "flame",
		"rarity": "rare",
		"category": "streak",
		"is_hidden": False,
		"is_active": True,
		"sort_order": 90,
		"criteria": {"type": "streak_days", "count": 7},
	},
	{
		"id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
		"name": "XP Hunter",
		"icon": "flash-outline",
		"description": "Earn 1,000 XP.",
		"icon_url": "flash-outline",
		"rarity": "rare",
		"category": "progression",
		"is_hidden": False,
		"is_active": True,
		"sort_order": 100,
		"criteria": {"type": "xp_total", "count": 1000},
	},
	{
		"id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
		"name": "Level Climber",
		"icon": "trending-up-outline",
		"description": "Reach level 5.",
		"icon_url": "trending-up-outline",
		"rarity": "epic",
		"category": "progression",
		"is_hidden": False,
		"is_active": True,
		"sort_order": 110,
		"criteria": {"type": "level_reached", "count": 5},
	},
	{
		"id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
		"name": "Trusted Explorer",
		"icon": "shield-checkmark-outline",
		"description": "Get 10 submissions approved.",
		"icon_url": "shield-checkmark-outline",
		"rarity": "epic",
		"category": "trust",
		"is_hidden": False,
		"is_active": True,
		"sort_order": 120,
		"criteria": {"type": "approved_submissions", "count": 10},
	},
]


def upgrade() -> None:
	badges_table = sa.table(
		"badges",
		sa.column("id", UUID(as_uuid=True)),
		sa.column("name", sa.String()),
		sa.column("icon", sa.String()),
		sa.column("criteria", sa.JSON()),
	)
	bind = op.get_bind()
	existing_rows = bind.execute(sa.text("SELECT name FROM badges")).fetchall()
	existing_names = {row[0] for row in existing_rows}
	rows = [
		{
			"id": __import__("uuid").UUID(badge["id"]),
			"name": badge["name"],
			"icon": badge["icon"],
			"criteria": badge["criteria"],
		}
		for badge in BADGES
		if badge["name"] not in existing_names
	]
	if rows:
		op.bulk_insert(badges_table, rows)


def downgrade() -> None:
	names = [badge["name"] for badge in BADGES]
	op.execute(
		sa.text("DELETE FROM badges WHERE name IN :names").bindparams(
			sa.bindparam("names", expanding=True, value=names)
		)
	)
