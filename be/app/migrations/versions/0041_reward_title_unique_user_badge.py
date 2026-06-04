"""Add unique constraint on user_badges

Revision ID: 0041_reward_title_unique_user_badge
Revises: 0040_expand_badges_schema
Create Date: 2026-05-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0041_reward_title_unique_user_badge"
down_revision = "0040_expand_badges_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
	# Add unique constraint on user_badges(user_id, badge_id) to prevent duplicates
	# Use try/except to be safe if constraint already exists
	try:
		op.create_unique_constraint(
			"uq_user_badges_user_badge",
			"user_badges",
			["user_id", "badge_id"],
		)
	except Exception:
		pass  # Constraint may already exist in some environments


def downgrade() -> None:
	try:
		op.drop_constraint("uq_user_badges_user_badge", "user_badges", type_="unique")
	except Exception:
		pass
