"""merge quest and post migrations

Revision ID: 867151d11173
Revises: 0054_add_is_event_to_quests, fd3149538e98
Create Date: 2026-06-16 15:57:09.938030

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '867151d11173'
down_revision = ('0054_add_is_event_to_quests', 'fd3149538e98')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
