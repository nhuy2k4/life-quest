from __future__ import annotations

import argparse
import asyncio
import uuid

from sqlalchemy import delete, or_, select, text

from app.core.database import AsyncSessionLocal
from app.models.auth import RefreshToken
from app.models.notification import Notification, UserPushToken
from app.models.recommendation import RecommendationLog
from app.models.social import Comment, Follow, Like, Post
from app.models.submission import Submission
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.user_quest import UserQuest
from app.models.xp_transaction import XpTransaction


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reset one user's data while keeping login account intact.",
    )
    parser.add_argument("identifier", help="User id, username, or email.")
    parser.add_argument("--yes", action="store_true", help="Required confirmation flag.")
    parser.add_argument("--keep-sessions", action="store_true", help="Keep refresh tokens and push tokens.")
    return parser.parse_args()


async def reset_user_data(identifier: str, *, keep_sessions: bool) -> None:
    async with AsyncSessionLocal() as session:
        user_id: uuid.UUID | None = None

        try:
            user_id = uuid.UUID(identifier)
        except ValueError:
            user_id = None

        user = await session.scalar(
            select(User).where(
                or_(
                    User.id == user_id if user_id else text("false"),
                    User.username == identifier,
                    User.email == identifier,
                )
            )
        )

        if user is None:
            print(f"[ERROR] User not found: {identifier}")
            return

        print(f"[INFO] Resetting data for user: {user.username} ({user.id})")

        user_quest_ids = select(UserQuest.id).where(UserQuest.user_id == user.id)

        submission_ids = select(Submission.id).where(
            Submission.user_quest_id.in_(user_quest_ids)
        )

        post_ids = select(Post.id).where(Post.user_id == user.id)

        # Delete child tables first
        await session.execute(
            delete(XpTransaction).where(
                or_(
                    XpTransaction.user_id == user.id,
                    XpTransaction.submission_id.in_(submission_ids),
                )
            )
        )

        # Social content related to this user
        await session.execute(
            delete(Comment).where(
                or_(
                    Comment.user_id == user.id,
                    Comment.post_id.in_(post_ids),
                )
            )
        )

        await session.execute(
            delete(Like).where(
                or_(
                    Like.user_id == user.id,
                    Like.post_id.in_(post_ids),
                )
            )
        )

        await session.execute(delete(Post).where(Post.user_id == user.id))

        await session.execute(
            delete(Follow).where(
                or_(
                    Follow.follower_id == user.id,
                    Follow.following_id == user.id,
                )
            )
        )

        # Gameplay
        await session.execute(
            delete(Submission).where(
                Submission.id.in_(submission_ids)
            )
        )

        await session.execute(
            delete(UserQuest).where(UserQuest.user_id == user.id)
        )

        # User state
        await session.execute(
            delete(UserPreference).where(UserPreference.user_id == user.id)
        )

        await session.execute(
            delete(Notification).where(Notification.user_id == user.id)
        )

        # Recommendation
        await session.execute(
            delete(RecommendationLog).where(RecommendationLog.user_id == user.id)
        )

        # Sessions
        if not keep_sessions:
            await session.execute(
                delete(RefreshToken).where(RefreshToken.user_id == user.id)
            )

            await session.execute(
                delete(UserPushToken).where(UserPushToken.user_id == user.id)
            )

        # Reset progression
        user.level_id = 1
        user.xp = 0
        user.streak_days = 0
        user.trust_score = 1.0

        await session.commit()

        print("[DONE] User data reset complete.")
        print("[RESET] quests, submissions, XP, social data, recommendations, notifications.")
        if keep_sessions:
            print("[KEPT] refresh tokens and push tokens.")
        else:
            print("[RESET] sessions and push tokens cleared.")


async def main() -> None:
    args = parse_args()

    if not args.yes:
        print("[ABORT] Add --yes to confirm.")
        return

    await reset_user_data(
        args.identifier,
        keep_sessions=args.keep_sessions,
    )


if __name__ == "__main__":
    asyncio.run(main())
