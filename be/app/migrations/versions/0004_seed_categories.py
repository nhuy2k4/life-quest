"""Seed initial categories

Revision ID: 0004_seed_categories
Revises: 0003_add_is_verified_to_users
Create Date: 2026-04-07 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0004_seed_categories'
down_revision = '0003_add_is_verified_to_users'
branch_labels = None
depends_on = None

def upgrade():
    # Insert initial categories
    op.bulk_insert(
        sa.table(
            'categories',
            sa.column('id', sa.Integer),
            sa.column('name', sa.String),
            sa.column('icon', sa.String),
        ),
        [
            {'id': 1, 'name': 'Sức khỏe', 'icon': 'health'},
            {'id': 2, 'name': 'Học tập', 'icon': 'study'},
            {'id': 3, 'name': 'Thể thao', 'icon': 'sports'},
            {'id': 4, 'name': 'Kỹ năng', 'icon': 'skills'},
            {'id': 5, 'name': 'Giải trí', 'icon': 'entertainment'},
        ]
    )

def downgrade():
    op.execute("DELETE FROM categories WHERE id IN (1,2,3,4,5)")
