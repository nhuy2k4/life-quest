"""Reset one user's runtime data while keeping the login account.

Usage:
    python admin_reset_one_user_data.py <username-or-email-or-user-id> --yes

By default this keeps the fields needed to keep the account usable:
username, email, password_hash, provider/provider_id, role, is_verified, is_banned.
It clears gameplay/social/session data and resets XP counters.
It keeps onboarding_completed so the account can continue using quest flows.
"""

from __future__ import annotations

import argparse
import asyncio
import uuid

from sqlalchemy import delete, or_, select, text

from app.core.database import AsyncSessionLocal
from app.models.auth import RefreshToken
from app.models.audit import AuditLog, RewardLog, SubmissionReview, UserEvent
from app.models.badge import UserBadge
from app.models.notification import Notification, UserPushToken
from app.models.recommendation import RecommendationLog, UserAiStats, UserQuestStats
from app.models.social import Comment, Follow, Like, Post
from app.models.submission import Submission
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.user_quest import UserQuest
from app.models.xp_transaction import XpTransaction


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset one user's data, keeping username/password login intact.",
    )
    parser.add_argument(
        "identifier",
        help="User id, username, or email.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Required confirmation flag.",
    )
    parser.add_argument(
        "--reset-email",
        action="store_true",
        help="Also reset email to <username>@reset.local. Use only if you really want email cleared.",
    )
    parser.add_argument(
        "--keep-sessions",
        action="store_true",
        help="Keep refresh tokens and push tokens instead of logging the user out.",
    )
    return parser.parse_args()


async def find_user(identifier: str) -> User | None:
    async with AsyncSessionLocal() as session:
        user_id: uuid.UUID | None = None
        try:
            user_id = uuid.UUID(identifier)
        except ValueError:
            user_id = None

        stmt = select(User).where(
            or_(
                User.id == user_id if user_id is not None else text("false"),
                User.username == identifier,
                User.email == identifier,
            )
        )
        return await session.scalar(stmt)


async def reset_user_data(identifier: str, *, reset_email: bool, keep_sessions: bool) -> None:
    async with AsyncSessionLocal() as session:
        user_id: uuid.UUID | None = None
        try:
            user_id = uuid.UUID(identifier)
        except ValueError:
            user_id = None

        user = await session.scalar(
            select(User).where(
                or_(
                    User.id == user_id if user_id is not None else text("false"),
                    User.username == identifier,
                    User.email == identifier,
                )
            )
        )
        if user is None:
            print(f"[ERROR] User not found: {identifier}")
            return

        print(f"[INFO] Resetting data for user: {user.username} ({user.id})")

        # Tables that reference submissions/user_quests need to go before deleting user_quests.
        user_quest_ids = select(UserQuest.id).where(UserQuest.user_id == user.id)
        submission_ids = select(Submission.id).where(Submission.user_quest_id.in_(user_quest_ids))

        await session.execute(delete(SubmissionReview).where(SubmissionReview.submission_id.in_(submission_ids)))
        await session.execute(delete(RewardLog).where(RewardLog.user_id == user.id))
        await session.execute(delete(XpTransaction).where(XpTransaction.user_id == user.id))

        # Social graph and content.
        post_ids = select(Post.id).where(Post.user_id == user.id)
        await session.execute(delete(Comment).where(or_(Comment.user_id == user.id, Comment.post_id.in_(post_ids))))
        await session.execute(delete(Like).where(or_(Like.user_id == user.id, Like.post_id.in_(post_ids))))
        await session.execute(delete(Post).where(Post.user_id == user.id))
        await session.execute(delete(Follow).where(or_(Follow.follower_id == user.id, Follow.following_id == user.id)))

        # Quest attempts cascade to submissions via FK.
        await session.execute(delete(UserQuest).where(UserQuest.user_id == user.id))

        # Personal app state.
        await session.execute(delete(UserPreference).where(UserPreference.user_id == user.id))
        await session.execute(delete(UserBadge).where(UserBadge.user_id == user.id))
        await session.execute(delete(Notification).where(Notification.user_id == user.id))
        await session.execute(delete(UserEvent).where(UserEvent.user_id == user.id))
        await session.execute(delete(AuditLog).where(AuditLog.actor_id == user.id))

        # Recommendation/profile stats.
        await session.execute(delete(RecommendationLog).where(RecommendationLog.user_id == user.id))
        await session.execute(delete(UserQuestStats).where(UserQuestStats.user_id == user.id))
        await session.execute(delete(UserAiStats).where(UserAiStats.user_id == user.id))

        if not keep_sessions:
            await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user.id))
            await session.execute(delete(UserPushToken).where(UserPushToken.user_id == user.id))

        # Keep username/password_hash and account ownership fields.
        user.level_id = 1
        user.xp = 0
        user.streak_days = 0
        user.trust_score = 1.0

        if reset_email:
            user.email = f"{user.username}@reset.local"

        await session.commit()
        print("[DONE] User data reset complete.")
        print("[KEPT] username, password_hash, provider/provider_id, role, verification/ban flags, onboarding status.")
        if keep_sessions:
            print("[KEPT] refresh tokens and push tokens because --keep-sessions was used.")
        else:
            print("[RESET] sessions and push tokens cleared; user must log in again.")


async def main() -> None:
    args = parse_args()
    if not args.yes:
        print("[ABORT] Add --yes to confirm this destructive reset.")
        return

    await reset_user_data(
        args.identifier,
        reset_email=args.reset_email,
        keep_sessions=args.keep_sessions,
    )


if __name__ == "__main__":
    asyncio.run(main())
