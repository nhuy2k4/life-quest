"""Add POI table and AI quest fields

Revision ID: 0013_add_poi_and_ai_schema
Revises: 0012_add_vision_spec_to_quests
Create Date: 2026-05-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0013_add_poi_and_ai_schema"
down_revision = "0012_add_vision_spec_to_quests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE submission_status_enum ADD VALUE IF NOT EXISTS 'processing'")

    op.create_table(
        "pois",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("poi_type", sa.String(50), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("radius_m", sa.Float(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(64), nullable=True),
        sa.Column("external_type", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_pois_lat_lng", "pois", ["latitude", "longitude"])

    op.add_column("quests", sa.Column("template", sa.String(255), nullable=True))
    op.add_column("quests", sa.Column("labels", sa.JSON(), nullable=True))
    op.add_column("quests", sa.Column("label_rules", sa.JSON(), nullable=True))
    op.add_column("quests", sa.Column("min_confidence", sa.Float(), nullable=True))
    op.add_column(
        "quests",
        sa.Column("poi_id", UUID(as_uuid=True), sa.ForeignKey("pois.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_quests_poi_id", "quests", ["poi_id"])

    op.add_column("submissions", sa.Column("vision_labels", sa.JSON(), nullable=True))
    op.add_column("submissions", sa.Column("vision_raw", sa.JSON(), nullable=True))
    op.add_column("submissions", sa.Column("lat", sa.Float(), nullable=True))
    op.add_column("submissions", sa.Column("lng", sa.Float(), nullable=True))
    op.add_column("submissions", sa.Column("location_accuracy_m", sa.Float(), nullable=True))
    op.add_column("submissions", sa.Column("location_captured_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "submissions",
        sa.Column("poi_id", UUID(as_uuid=True), sa.ForeignKey("pois.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column("submissions", sa.Column("poi_distance_m", sa.Float(), nullable=True))
    op.add_column("submissions", sa.Column("prev_distance_m", sa.Float(), nullable=True))
    op.add_column("submissions", sa.Column("time_delta_s", sa.Float(), nullable=True))
    op.create_index("ix_submissions_poi_id", "submissions", ["poi_id"])


def downgrade() -> None:
    op.drop_index("ix_submissions_poi_id", table_name="submissions")
    op.drop_column("submissions", "time_delta_s")
    op.drop_column("submissions", "prev_distance_m")
    op.drop_column("submissions", "poi_distance_m")
    op.drop_column("submissions", "poi_id")
    op.drop_column("submissions", "location_captured_at")
    op.drop_column("submissions", "location_accuracy_m")
    op.drop_column("submissions", "lng")
    op.drop_column("submissions", "lat")
    op.drop_column("submissions", "vision_raw")
    op.drop_column("submissions", "vision_labels")

    op.drop_index("ix_quests_poi_id", table_name="quests")
    op.drop_column("quests", "poi_id")
    op.drop_column("quests", "min_confidence")
    op.drop_column("quests", "label_rules")
    op.drop_column("quests", "labels")
    op.drop_column("quests", "template")

    op.drop_index("ix_pois_lat_lng", table_name="pois")
    op.drop_table("pois")

    # Enum downgrade for submission_status_enum is not supported safely.
