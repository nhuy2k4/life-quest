"""Normalize user_quests status values

Revision ID: 0007_normalize_user_quest_status
Revises: 0006_seed_quest_categories
Create Date: 2026-04-07 21:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_normalize_user_quest_status"
down_revision = "0006_seed_quest_categories"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Convert legacy status to canonical value.
    op.execute("""
        UPDATE user_quests
        SET status = 'started'
        WHERE status = 'in_progress'
    """)

    op.alter_column(
        "user_quests",
        "status",
        existing_type=sa.String(length=20),
        server_default="started",
        nullable=False,
    )

    op.create_check_constraint(
        "ck_user_quests_status",
        "user_quests",
        "status IN ('not_started', 'started', 'submitted', 'approved', 'rejected')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_user_quests_status", "user_quests", type_="check")

    op.execute("""
        UPDATE user_quests
        SET status = 'in_progress'
        WHERE status = 'started'
    """)

    op.alter_column(
        "user_quests",
        "status",
        existing_type=sa.String(length=20),
        server_default="in_progress",
        nullable=False,
    )
