"""Initial tables

Revision ID: 0001_initial_tables
Revises: 
Create Date: 2026-04-03 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '0001_initial_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ── Levels (static seed data) ─────────────────────────────────────────
    op.create_table(
        'levels',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('required_xp', sa.Integer(), nullable=False),
    )
    op.bulk_insert(
        sa.table('levels',
            sa.column('id', sa.Integer),
            sa.column('name', sa.String),
            sa.column('required_xp', sa.Integer),
        ),
        [
            {'id': 1,  'name': 'Beginner',     'required_xp': 0},
            {'id': 2,  'name': 'Explorer',     'required_xp': 100},
            {'id': 3,  'name': 'Adventurer',   'required_xp': 300},
            {'id': 4,  'name': 'Challenger',   'required_xp': 600},
            {'id': 5,  'name': 'Hero',         'required_xp': 1000},
            {'id': 6,  'name': 'Champion',     'required_xp': 1500},
            {'id': 7,  'name': 'Legend',       'required_xp': 2200},
            {'id': 8,  'name': 'Mythic',       'required_xp': 3000},
            {'id': 9,  'name': 'Immortal',     'required_xp': 4000},
            {'id': 10, 'name': 'Transcendent', 'required_xp': 5500},
        ]
    )

    # ── Users ─────────────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(50), nullable=False, unique=True),
        sa.Column('email', sa.String(100), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('provider', sa.String(20), nullable=False, server_default='local'),
        sa.Column('provider_id', sa.String(255), nullable=True),
        sa.Column('level_id', sa.Integer(), sa.ForeignKey('levels.id'), default=1),
        sa.Column('xp', sa.Integer(), nullable=False, default=0),
        sa.Column('streak_days', sa.Integer(), nullable=False, default=0),
        sa.Column('trust_score', sa.Float(), nullable=False, default=1.0),
        sa.Column('role', sa.String(20), nullable=False, default='user'),
        sa.Column('is_banned', sa.Boolean(), nullable=False, default=False),
        sa.Column('onboarding_completed', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_users_provider_id', 'users', ['provider_id'])

    # ── Refresh Tokens ────────────────────────────────────────────────────
    op.create_table(
        'refresh_tokens',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, default=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_refresh_tokens_user_id', 'refresh_tokens', ['user_id'])

    # ── User Preferences ──────────────────────────────────────────────────
    op.create_table(
        'user_preferences',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('interests', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('interest_weights', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('activity_level', sa.String(20), nullable=True),
        sa.Column('location_enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('notification_enabled', sa.Boolean(), nullable=False, default=True),
    )

    # ── Categories ────────────────────────────────────────────────────────
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('icon', sa.String(100), nullable=True),
    )

    # ── Quests ────────────────────────────────────────────────────────────
    op.create_table(
        'quests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('xp_reward', sa.Integer(), nullable=False, default=50),
        sa.Column('difficulty', sa.String(20), nullable=False, default='medium'),
        sa.Column('approval_rate', sa.Float(), nullable=False, default=1.0),
        sa.Column('time_limit_hours', sa.Integer(), nullable=True),
        sa.Column('location_required', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_quests_is_active', 'quests', ['is_active'])

    # ── Quest Categories (M:N junction) ───────────────────────────────────
    op.create_table(
        'quest_categories',
        sa.Column('quest_id', UUID(as_uuid=True), sa.ForeignKey('quests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False),
        sa.PrimaryKeyConstraint('quest_id', 'category_id'),
    )

    # ── User Quests ───────────────────────────────────────────────────────
    op.create_table(
        'user_quests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quest_id', UUID(as_uuid=True), sa.ForeignKey('quests.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='in_progress'),
        sa.Column('started_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('user_id', 'quest_id', name='uq_user_quests_user_quest'),
    )
    op.create_index('ix_user_quests_user_status', 'user_quests', ['user_id', 'status'])

    # ── Submissions ───────────────────────────────────────────────────────
    op.create_table(
        'submissions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_quest_id', UUID(as_uuid=True), sa.ForeignKey('user_quests.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('image_url', sa.String(500), nullable=False),
        sa.Column('cloudinary_public_id', sa.String(255), nullable=False),
        sa.Column('file_hash', sa.String(64), nullable=False),
        sa.Column('exif_data', sa.JSON(), nullable=True),
        sa.Column('cheat_flags', sa.JSON(), nullable=True),
        sa.Column('ai_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('is_suspicious', sa.Boolean(), nullable=False, default=False),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_submissions_status', 'submissions', ['status'])
    op.create_index('ix_submissions_file_hash', 'submissions', ['file_hash'])
    op.create_index('ix_submissions_suspicious', 'submissions', ['is_suspicious'])

    # ── Badges ────────────────────────────────────────────────────────────
    op.create_table(
        'badges',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('icon', sa.String(100), nullable=True),
        sa.Column('criteria', sa.JSON(), nullable=False),
    )

    # ── User Badges ───────────────────────────────────────────────────────
    op.create_table(
        'user_badges',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('badge_id', UUID(as_uuid=True), sa.ForeignKey('badges.id', ondelete='CASCADE'), nullable=False),
        sa.Column('earned_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'badge_id', name='uq_user_badges_user_badge'),
    )
    op.create_index('ix_user_badges_user_id', 'user_badges', ['user_id'])

    # ── XP Transactions (immutable audit log) ─────────────────────────────
    op.create_table(
        'xp_transactions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submission_id', UUID(as_uuid=True), sa.ForeignKey('submissions.id'), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(50), nullable=False, default='quest_approved'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_xp_transactions_user_id', 'xp_transactions', ['user_id'])
    op.create_index('ix_xp_transactions_submission_id', 'xp_transactions', ['submission_id'])

    # ── Follows ───────────────────────────────────────────────────────────
    op.create_table(
        'follows',
        sa.Column('follower_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('following_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('follower_id', 'following_id'),
    )
    op.create_index('ix_follows_following_id', 'follows', ['following_id'])

    # ── Posts ─────────────────────────────────────────────────────────────
    op.create_table(
        'posts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', UUID(as_uuid=True), sa.ForeignKey('submissions.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('like_count', sa.Integer(), nullable=False, default=0),
        sa.Column('comment_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_posts_user_id', 'posts', ['user_id'])
    op.create_index('ix_posts_created_at', 'posts', ['created_at'])

    # ── Likes ─────────────────────────────────────────────────────────────
    op.create_table(
        'likes',
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('post_id', UUID(as_uuid=True), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('user_id', 'post_id'),
    )
    op.create_index('ix_likes_post_id', 'likes', ['post_id'])

    # ── Comments ──────────────────────────────────────────────────────────
    op.create_table(
        'comments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('post_id', UUID(as_uuid=True), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_id', UUID(as_uuid=True), sa.ForeignKey('comments.id'), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_comments_post_id', 'comments', ['post_id'])
    op.create_index('ix_comments_parent_id', 'comments', ['parent_id'])

    # ── Notifications ─────────────────────────────────────────────────────
    op.create_table(
        'notifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_notifications_user_unread', 'notifications', ['user_id', 'is_read'])


def downgrade():
    # Drop indexes trước
    op.drop_index('ix_notifications_user_unread')
    op.drop_index('ix_comments_parent_id')
    op.drop_index('ix_comments_post_id')
    op.drop_index('ix_likes_post_id')
    op.drop_index('ix_posts_created_at')
    op.drop_index('ix_posts_user_id')
    op.drop_index('ix_follows_following_id')
    op.drop_index('ix_xp_transactions_submission_id')
    op.drop_index('ix_xp_transactions_user_id')
    op.drop_index('ix_user_badges_user_id')
    op.drop_index('ix_submissions_suspicious')
    op.drop_index('ix_submissions_file_hash')
    op.drop_index('ix_users_provider_id')
    op.drop_index('ix_submissions_status')
    op.drop_index('ix_user_quests_user_status')
    op.drop_index('ix_quests_is_active')
    op.drop_index('ix_refresh_tokens_user_id')

    # Drop tables theo thứ tự phụ thuộc FK
    tables = [
        'notifications', 'comments', 'likes', 'posts', 'follows',
        'xp_transactions', 'user_badges', 'badges', 'submissions',
        'user_quests', 'quest_categories', 'quests', 'categories',
        'user_preferences', 'refresh_tokens', 'users', 'levels',
    ]
    for table in tables:
        op.drop_table(table)