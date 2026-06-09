"""Drop unused submission columns

Revision ID: 0050_drop_unused_submission_columns
Revises: 0049_cleanup_invalid_event_posts
Create Date: 2026-06-08

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0050_drop_unused_submission_columns"
down_revision = "0049_cleanup_invalid_event_posts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("submissions", "time_delta_s")
    op.drop_column("submissions", "prev_distance_m")
    op.drop_column("submissions", "exif_data")


def downgrade() -> None:
    op.add_column("submissions", sa.Column("exif_data", sa.JSON(), nullable=True))
    op.add_column("submissions", sa.Column("prev_distance_m", sa.Float(), nullable=True))
    op.add_column("submissions", sa.Column("time_delta_s", sa.Float(), nullable=True))
