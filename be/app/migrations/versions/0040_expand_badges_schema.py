"""Expand badges schema

Revision ID: 0040_expand_badges_schema
Revises: 0039_seed_badges
Create Date: 2026-05-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0040_expand_badges_schema"
down_revision = "0039_seed_badges"
branch_labels = None
depends_on = None


BADGE_METADATA = {
	"First Quest": {
		"description": "Complete your first quest.",
		"icon_url": "flag-outline",
		"rarity": "common",
		"category": "quests",
		"is_hidden": False,
		"sort_order": 10,
	},
	"Quest Rookie": {
		"description": "Complete 5 quests.",
		"icon_url": "walk-outline",
		"rarity": "common",
		"category": "quests",
		"is_hidden": False,
		"sort_order": 20,
	},
	"Quest Pro": {
		"description": "Complete 20 quests.",
		"icon_url": "trophy-outline",
		"rarity": "rare",
		"category": "quests",
		"is_hidden": False,
		"sort_order": 30,
	},
	"Century Explorer": {
		"description": "Complete 100 quests.",
		"icon_url": "ribbon-outline",
		"rarity": "legendary",
		"category": "quests",
		"is_hidden": True,
		"sort_order": 40,
	},
	"First Post": {
		"description": "Share your first post.",
		"icon_url": "image-outline",
		"rarity": "common",
		"category": "social",
		"is_hidden": False,
		"sort_order": 50,
	},
	"Social Spark": {
		"description": "Write 10 comments.",
		"icon_url": "chatbubbles-outline",
		"rarity": "common",
		"category": "social",
		"is_hidden": False,
		"sort_order": 60,
	},
	"Community Favorite": {
		"description": "Receive 25 likes across your posts.",
		"icon_url": "heart-outline",
		"rarity": "rare",
		"category": "social",
		"is_hidden": False,
		"sort_order": 70,
	},
	"Streak Starter": {
		"description": "Reach a 3-day streak.",
		"icon_url": "flame-outline",
		"rarity": "common",
		"category": "streak",
		"is_hidden": False,
		"sort_order": 80,
	},
	"On Fire": {
		"description": "Reach a 7-day streak.",
		"icon_url": "flame",
		"rarity": "rare",
		"category": "streak",
		"is_hidden": False,
		"sort_order": 90,
	},
	"XP Hunter": {
		"description": "Earn 1,000 XP.",
		"icon_url": "flash-outline",
		"rarity": "rare",
		"category": "progression",
		"is_hidden": False,
		"sort_order": 100,
	},
	"Level Climber": {
		"description": "Reach level 5.",
		"icon_url": "trending-up-outline",
		"rarity": "epic",
		"category": "progression",
		"is_hidden": False,
		"sort_order": 110,
	},
	"Trusted Explorer": {
		"description": "Get 10 submissions approved.",
		"icon_url": "shield-checkmark-outline",
		"rarity": "epic",
		"category": "trust",
		"is_hidden": False,
		"sort_order": 120,
	},
}


def upgrade() -> None:
	op.add_column("badges", sa.Column("description", sa.Text(), nullable=False, server_default=""))
	op.add_column("badges", sa.Column("icon_url", sa.String(length=255), nullable=False, server_default=""))
	op.add_column("badges", sa.Column("rarity", sa.String(length=30), nullable=False, server_default="common"))
	op.add_column("badges", sa.Column("category", sa.String(length=50), nullable=False, server_default="general"))
	op.add_column("badges", sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.text("false")))
	op.add_column("badges", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
	op.add_column("badges", sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")))
	op.add_column("badges", sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
	op.add_column("badges", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))

	for name, metadata in BADGE_METADATA.items():
		op.execute(
			sa.text(
				"""
				UPDATE badges
				SET description = :description,
					icon_url = COALESCE(NULLIF(icon, ''), :icon_url),
					rarity = :rarity,
					category = :category,
					is_hidden = :is_hidden,
					is_active = true,
					sort_order = :sort_order,
					updated_at = now()
				WHERE name = :name
				"""
			).bindparams(name=name, **metadata)
		)

	op.drop_column("badges", "icon")
	op.create_index("ix_badges_category", "badges", ["category"])
	op.create_index("ix_badges_rarity", "badges", ["rarity"])
	op.create_index("ix_badges_active_sort", "badges", ["is_active", "sort_order"])


def downgrade() -> None:
	op.add_column("badges", sa.Column("icon", sa.String(length=100), nullable=True))
	op.execute("UPDATE badges SET icon = icon_url")
	op.drop_index("ix_badges_active_sort", table_name="badges")
	op.drop_index("ix_badges_rarity", table_name="badges")
	op.drop_index("ix_badges_category", table_name="badges")
	for column_name in (
		"updated_at",
		"created_at",
		"sort_order",
		"is_active",
		"is_hidden",
		"category",
		"rarity",
		"icon_url",
		"description",
	):
		op.drop_column("badges", column_name)
