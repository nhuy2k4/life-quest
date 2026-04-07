"""Convert user_preferences interests to JSON

Revision ID: 0008_interests_json
Revises: 0007_normalize_user_quest_status
Create Date: 2026-04-07 22:15:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0008_interests_json"
down_revision = "0007_normalize_user_quest_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Old defaults like '{}' can block type cast; remove them before ALTER TYPE.
    op.execute(
        """
        ALTER TABLE user_preferences
        ALTER COLUMN interests DROP DEFAULT,
        ALTER COLUMN interest_weights DROP DEFAULT
        """
    )

    # Convert interests from int[] to json and keep existing values.
    op.execute(
        """
        ALTER TABLE user_preferences
        ALTER COLUMN interests TYPE json USING to_json(interests)
        """
    )

    # Convert JSONB weights to JSON for cross-database compatibility.
    op.execute(
        """
        ALTER TABLE user_preferences
        ALTER COLUMN interest_weights TYPE json USING interest_weights::json
        """
    )

    op.alter_column(
        "user_preferences",
        "interests",
        existing_type=sa.JSON(),
        server_default=sa.text("'[]'::json"),
        nullable=False,
    )
    op.alter_column(
        "user_preferences",
        "interest_weights",
        existing_type=sa.JSON(),
        server_default=sa.text("'{}'::json"),
        nullable=False,
    )


def downgrade() -> None:
    # Remove JSON defaults before casting back.
    op.execute(
        """
        ALTER TABLE user_preferences
        ALTER COLUMN interests DROP DEFAULT,
        ALTER COLUMN interest_weights DROP DEFAULT
        """
    )

    # Revert interests back to integer array.
    op.execute(
        """
        ALTER TABLE user_preferences
        ALTER COLUMN interests TYPE integer[]
        USING (
            ARRAY(
                SELECT json_array_elements_text(interests)::integer
            )
        )
        """
    )

    # Revert weights back to JSONB.
    op.execute(
        """
        ALTER TABLE user_preferences
        ALTER COLUMN interest_weights TYPE jsonb USING interest_weights::jsonb
        """
    )

    op.alter_column(
        "user_preferences",
        "interests",
        existing_type=sa.ARRAY(sa.Integer()),
        server_default=sa.text("'{}'::integer[]"),
        nullable=False,
    )
    op.alter_column(
        "user_preferences",
        "interest_weights",
        existing_type=postgresql.JSONB(),
        server_default=sa.text("'{}'::jsonb"),
        nullable=False,
    )
