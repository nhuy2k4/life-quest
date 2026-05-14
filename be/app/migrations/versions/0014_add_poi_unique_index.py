"""Add unique index for OSM upsert

Revision ID: 0014_add_poi_unique_index
Revises: 0013_add_poi_and_ai_schema
Create Date: 2026-05-06 00:00:00.000000
"""

from alembic import op

revision = "0014_add_poi_unique_index"
down_revision = "0013_add_poi_and_ai_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_pois_source_external_id",
        "pois",
        ["source", "external_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_pois_source_external_id", "pois", type_="unique")
