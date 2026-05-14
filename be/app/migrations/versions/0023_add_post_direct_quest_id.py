"""Add direct quest_id to post

Revision ID: 0023_add_post_direct_quest_id
Revises: 0022_add_standalone_post_fields
Create Date: 2026-05-12 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '0023_add_post_direct_quest_id'
down_revision = '0022_add_standalone_post_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('posts', sa.Column('quest_id', UUID(as_uuid=True), sa.ForeignKey('quests.id', ondelete='SET NULL'), nullable=True))
    op.create_index('ix_posts_quest_id', 'posts', ['quest_id'])


def downgrade() -> None:
    op.drop_index('ix_posts_quest_id', table_name='posts')
    op.drop_column('posts', 'quest_id')
