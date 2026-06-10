"""Drop more unused nullable columns

Revision ID: 0051_drop_more_unused_columns
Revises: 0050_drop_unused_submission_columns
Create Date: 2026-06-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0051_drop_more_unused_columns"
down_revision = "0050_drop_unused_submission_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("ai_detection_logs", "model_version")
    op.drop_column("ai_detection_logs", "ocr_text")
    op.drop_column("quests", "vision_spec")
    op.drop_column("submissions", "location_captured_at")


def downgrade() -> None:
    op.add_column("submissions", sa.Column("location_captured_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("quests", sa.Column("vision_spec", sa.JSON(), nullable=True))
    op.add_column("ai_detection_logs", sa.Column("ocr_text", sa.Text(), nullable=True))
    op.add_column("ai_detection_logs", sa.Column("model_version", sa.String(length=50), nullable=True))
