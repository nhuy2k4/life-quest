"""add poi_id to event_quests

Revision ID: 0056_add_poi_id_to_event_quests
Revises: 0055_add_event_location
Create Date: 2026-06-17

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0056_add_poi_id_to_event_quests'
down_revision = '0055_add_event_location'
branch_labels = None
depends_on = None


def upgrade() -> None:
	op.add_column('event_quests', sa.Column('poi_id', sa.UUID(), sa.ForeignKey('pois.id', ondelete='SET NULL'), nullable=True))


def downgrade() -> None:
	op.drop_column('event_quests', 'poi_id')
