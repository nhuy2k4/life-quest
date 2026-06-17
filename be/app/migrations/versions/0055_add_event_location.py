"""add event location

Revision ID: 0055_add_event_location
Revises: 867151d11173
Create Date: 2026-06-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0055_add_event_location'
down_revision = '867151d11173'
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.add_column('events', sa.Column('location_name', sa.Text(), nullable=True))
	op.add_column('events', sa.Column('latitude', sa.Float(), nullable=True))
	op.add_column('events', sa.Column('longitude', sa.Float(), nullable=True))
	op.add_column('events', sa.Column('radius_m', sa.Float(), nullable=True))


def downgrade() -> None:
	op.drop_column('events', 'radius_m')
	op.drop_column('events', 'longitude')
	op.drop_column('events', 'latitude')
	op.drop_column('events', 'location_name')
