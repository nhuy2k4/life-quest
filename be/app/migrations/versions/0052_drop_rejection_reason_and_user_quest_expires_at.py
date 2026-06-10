"""Drop rejection reason and user quest expiry columns

Revision ID: 0052_drop_rejection_reason_expires_at
Revises: 0051_drop_more_unused_columns
Create Date: 2026-06-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0052_drop_rejection_reason_expires_at"
down_revision = "0051_drop_more_unused_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("submissions", "rejection_reason")
    op.drop_column("user_quests", "expires_at")


def downgrade() -> None:
    op.add_column("user_quests", sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("submissions", sa.Column("rejection_reason", sa.Text(), nullable=True))
