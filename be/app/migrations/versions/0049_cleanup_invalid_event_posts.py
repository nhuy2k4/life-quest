"""Cleanup invalid event post links

Revision ID: 0049_cleanup_invalid_event_posts
Revises: 0048_chat_1_1_tables
Create Date: 2026-05-31
"""

from alembic import op


revision = "0049_cleanup_invalid_event_posts"
down_revision = "0048_chat_1_1_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.execute(
		"""
		UPDATE posts
		SET event_id = NULL
		WHERE event_id IS NOT NULL
		  AND (
			submission_id IS NULL
			OR NOT EXISTS (
				SELECT 1
				FROM submissions
				WHERE submissions.id = posts.submission_id
				  AND submissions.status = 'approved'
			)
		  )
		"""
	)


def downgrade() -> None:
	pass
