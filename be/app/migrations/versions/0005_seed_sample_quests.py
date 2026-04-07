"""Seed sample quests

Revision ID: 0005_seed_sample_quests
Revises: 0004_seed_categories
Create Date: 2026-04-07 20:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
import uuid
from datetime import datetime

revision = '0005_seed_sample_quests'
down_revision = '0004_seed_categories'
branch_labels = None
depends_on = None

def upgrade():
    now = datetime.utcnow()
    from sqlalchemy.dialects import postgresql
    quests = [
        {
            'id': uuid.uuid4(),
            'title': 'Uống 2 lít nước/ngày',
            'description': 'Theo dõi lượng nước uống đủ 2 lít trong ngày.',
            'xp_reward': 50,
            'difficulty': 'easy',
            'approval_rate': 1.0,
            'time_limit_hours': 24,
            'location_required': False,
            'is_active': True,
            'created_at': now,
            'updated_at': now,
        },
        {
            'id': uuid.uuid4(),
            'title': 'Đi bộ 10.000 bước',
            'description': 'Hoàn thành 10.000 bước chân trong 1 ngày.',
            'xp_reward': 70,
            'difficulty': 'medium',
            'approval_rate': 1.0,
            'time_limit_hours': 24,
            'location_required': False,
            'is_active': True,
            'created_at': now,
            'updated_at': now,
        },
        {
            'id': uuid.uuid4(),
            'title': 'Đọc sách 30 phút',
            'description': 'Đọc sách ít nhất 30 phút/ngày.',
            'xp_reward': 60,
            'difficulty': 'easy',
            'approval_rate': 1.0,
            'time_limit_hours': 24,
            'location_required': False,
            'is_active': True,
            'created_at': now,
            'updated_at': now,
        },
        {
            'id': uuid.uuid4(),
            'title': 'Tập thể dục 20 phút',
            'description': 'Tập thể dục liên tục ít nhất 20 phút.',
            'xp_reward': 80,
            'difficulty': 'medium',
            'approval_rate': 1.0,
            'time_limit_hours': 24,
            'location_required': False,
            'is_active': True,
            'created_at': now,
            'updated_at': now,
        },
        {
            'id': uuid.uuid4(),
            'title': 'Không dùng mạng xã hội 2 tiếng',
            'description': 'Không truy cập bất kỳ mạng xã hội nào trong 2 tiếng.',
            'xp_reward': 100,
            'difficulty': 'hard',
            'approval_rate': 1.0,
            'time_limit_hours': 24,
            'location_required': False,
            'is_active': True,
            'created_at': now,
            'updated_at': now,
        },
    ]
    op.bulk_insert(
        sa.table(
            'quests',
            sa.column('id', postgresql.UUID(as_uuid=True)),
            sa.column('title', sa.String),
            sa.column('description', sa.Text),
            sa.column('xp_reward', sa.Integer),
            sa.column('difficulty', sa.String),
            sa.column('approval_rate', sa.Float),
            sa.column('time_limit_hours', sa.Integer),
            sa.column('location_required', sa.Boolean),
            sa.column('is_active', sa.Boolean),
            sa.column('created_at', sa.DateTime),
            sa.column('updated_at', sa.DateTime),
        ),
        quests
    )

def downgrade():
    op.execute("DELETE FROM quests WHERE title IN ('Uống 2 lít nước/ngày', 'Đi bộ 10.000 bước', 'Đọc sách 30 phút', 'Tập thể dục 20 phút', 'Không dùng mạng xã hội 2 tiếng')")
