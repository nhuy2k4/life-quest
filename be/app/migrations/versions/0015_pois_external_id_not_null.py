"""Set external_id NOT NULL on pois

Revision ID: 0015_pois_external_id_not_null
Revises: 0014_add_poi_unique_index
Create Date: 2026-05-06 00:00:00.000000
"""

from alembic import op

revision = "0015_pois_external_id_not_null"
down_revision = "0014_add_poi_unique_index"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE pois SET external_id = id::text WHERE external_id IS NULL")
    op.alter_column("pois", "external_id", nullable=False)


def downgrade() -> None:
    op.alter_column("pois", "external_id", nullable=True)
