"""Schema hardening: constraints, indexes, audit tables

Revision ID: 0011_schema_hardening
Revises: 0010_drop_legacy_status
Create Date: 2026-04-30 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0011_schema_hardening"
down_revision = "0010_drop_legacy_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Constraints / FK updates ──────────────────────────────────────────
    op.create_unique_constraint(
        "uq_xp_transactions_submission",
        "xp_transactions",
        ["submission_id"],
    )

    op.alter_column("posts", "submission_id", nullable=True)

    op.drop_constraint("comments_parent_id_fkey", "comments", type_="foreignkey")
    op.create_foreign_key(
        "comments_parent_id_fkey",
        "comments",
        "comments",
        ["parent_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── Indexes ───────────────────────────────────────────────────────────
    op.create_index(
        "ix_submissions_status_created",
        "submissions",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_follows_follower_id",
        "follows",
        ["follower_id"],
    )
    op.create_index(
        "ix_posts_user_created",
        "posts",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_notifications_user_created",
        "notifications",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_comments_user_id",
        "comments",
        ["user_id"],
    )

    # ── New tables ────────────────────────────────────────────────────────
    op.create_table(
        "ai_detection_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("labels", sa.JSON(), nullable=True),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("confidence_stats", sa.JSON(), nullable=True),
        sa.Column("raw_response", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ai_detection_logs_submission", "ai_detection_logs", ["submission_id"])

    op.create_table(
        "submission_reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decision", sa.String(30), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_submission_reviews_submission", "submission_reviews", ["submission_id"])

    op.create_table(
        "reward_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submissions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reward_type", sa.String(30), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("submission_id", "reward_type", name="uq_reward_logs_submission_type"),
    )
    op.create_index("ix_reward_logs_user_id", "reward_logs", ["user_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_id", UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])

    op.create_table(
        "user_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_name", sa.String(100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_user_events_user_id", "user_events", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_events_user_id", table_name="user_events")
    op.drop_table("user_events")

    op.drop_index("ix_audit_logs_actor_id", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_reward_logs_user_id", table_name="reward_logs")
    op.drop_table("reward_logs")

    op.drop_index("ix_submission_reviews_submission", table_name="submission_reviews")
    op.drop_table("submission_reviews")

    op.drop_index("ix_ai_detection_logs_submission", table_name="ai_detection_logs")
    op.drop_table("ai_detection_logs")

    op.drop_index("ix_comments_user_id", table_name="comments")
    op.drop_index("ix_notifications_user_created", table_name="notifications")
    op.drop_index("ix_posts_user_created", table_name="posts")
    op.drop_index("ix_follows_follower_id", table_name="follows")
    op.drop_index("ix_submissions_status_created", table_name="submissions")

    op.drop_constraint("comments_parent_id_fkey", "comments", type_="foreignkey")
    op.create_foreign_key(
        "comments_parent_id_fkey",
        "comments",
        "comments",
        ["parent_id"],
        ["id"],
    )

    op.alter_column("posts", "submission_id", nullable=False)

    op.drop_constraint("uq_xp_transactions_submission", "xp_transactions", type_="unique")
