"""Rule based recommendation category slugs

Revision ID: 0027_reco_rule_categories
Revises: 0026_add_user_profile_fields
Create Date: 2026-05-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0027_reco_rule_categories"
down_revision = "0026_add_user_profile_fields"
branch_labels = None
depends_on = None


DEMO_CATEGORIES = [
	("food", "Food", "restaurant-outline"),
	("fitness", "Fitness", "barbell-outline"),
	("travel", "Travel", "map-outline"),
	("lifestyle", "Lifestyle", "sparkles-outline"),
	("community", "Community", "people-outline"),
	("photography", "Photography", "camera-outline"),
	("nature", "Nature", "leaf-outline"),
	("art", "Art", "color-palette-outline"),
	("music", "Music", "musical-notes-outline"),
	("reading", "Reading", "book-outline"),
	("cooking", "Cooking", "restaurant-outline"),
	("gaming", "Gaming", "game-controller-outline"),
]


def upgrade() -> None:
	op.add_column("categories", sa.Column("slug", sa.String(length=80), nullable=True))

	op.execute(
		"""
		UPDATE categories
		SET slug = CASE id
			WHEN 1 THEN 'health'
			WHEN 2 THEN 'study'
			WHEN 3 THEN 'sports'
			WHEN 4 THEN 'skills'
			WHEN 5 THEN 'entertainment'
			ELSE lower(regexp_replace(name, '[^a-zA-Z0-9]+', '-', 'g'))
		END
		WHERE slug IS NULL
		"""
	)

	for slug, name, icon in DEMO_CATEGORIES:
		op.execute(
			sa.text(
				"""
				INSERT INTO categories (slug, name, icon)
				SELECT :slug, :name, :icon
				WHERE NOT EXISTS (
					SELECT 1 FROM categories WHERE slug = :slug OR name = :name
				)
				"""
			).bindparams(slug=slug, name=name, icon=icon)
		)

	op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)
	op.add_column("recommendation_logs", sa.Column("section", sa.String(length=50), nullable=True))


def downgrade() -> None:
	op.drop_column("recommendation_logs", "section")
	op.drop_index("ix_categories_slug", table_name="categories")
	op.drop_column("categories", "slug")
