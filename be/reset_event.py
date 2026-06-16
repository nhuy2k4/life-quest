import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, delete, func, or_

from app.core.database import AsyncSessionLocal
from app.models.event import Event, EventResult, EventQuest
from app.models.enums import EventStatus, XpSource
from app.models.user import User
from app.models.badge import UserBadge
from app.models.user_quest import UserQuest
from app.models.social import Post, Like, Comment
from app.models.submission import Submission
from app.models.xp_transaction import XpTransaction
from app.models.auth import Level

async def main():
    event_id_arg = sys.argv[1] if len(sys.argv) > 1 else None
    
    async with AsyncSessionLocal() as session:
        if event_id_arg:
            # Get specific event
            result = await session.execute(
                select(Event).where(Event.id == event_id_arg)
            )
            event = result.scalar_one_or_none()
        else:
            # Get latest ended event first
            result = await session.execute(
                select(Event).where(Event.status == EventStatus.ENDED).order_by(Event.end_at.desc()).limit(1)
            )
            event = result.scalar_one_or_none()
            
            # Fallback to the latest event regardless of status (e.g. if already set to ACTIVE but dirty)
            if not event:
                result = await session.execute(
                    select(Event).order_by(Event.end_at.desc()).limit(1)
                )
                event = result.scalar_one_or_none()
            
        if not event:
            print("No suitable event found to reset.")
            return

        print(f"Resetting event: {event.title} (ID: {event.id})")
        
        # 1. Find all quest_ids for this event
        quest_ids_stmt = select(EventQuest.quest_id).where(EventQuest.event_id == event.id)
        quest_ids = (await session.scalars(quest_ids_stmt)).all()
        print(f"Found {len(quest_ids)} quest(s) belonging to this event.")

        # Get user_quest_ids list
        user_quest_ids = []
        if quest_ids:
            user_quest_ids_stmt = select(UserQuest.id).where(UserQuest.quest_id.in_(quest_ids))
            user_quest_ids = (await session.scalars(user_quest_ids_stmt)).all()
        print(f"Found {len(user_quest_ids)} active quest sessions (UserQuest).")

        # Get submission_ids list
        submission_ids = []
        if user_quest_ids:
            submission_ids_stmt = select(Submission.id).where(Submission.user_quest_id.in_(user_quest_ids))
            submission_ids = (await session.scalars(submission_ids_stmt)).all()
        print(f"Found {len(submission_ids)} submissions.")

        # Get all related post_ids
        post_ids_conditions = [Post.event_id == event.id]
        if quest_ids:
            post_ids_conditions.append(Post.quest_id.in_(quest_ids))
        if submission_ids:
            post_ids_conditions.append(Post.submission_id.in_(submission_ids))
        
        post_ids_stmt = select(Post.id).where(or_(*post_ids_conditions))
        post_ids = (await session.scalars(post_ids_stmt)).all()
        print(f"Found {len(post_ids)} posts related to this event/quests.")

        # 2. Revert XP and Badges from EventResult
        results_stmt = select(EventResult).where(EventResult.event_id == event.id)
        event_results = (await session.scalars(results_stmt)).all()
        print(f"Reverting XP and Badges for {len(event_results)} rewarded users...")
        
        for result in event_results:
            # 2a. Revert Badge
            if result.badge_id:
                deleted_badge = await session.execute(
                    delete(UserBadge).where(
                        UserBadge.user_id == result.user_id,
                        UserBadge.badge_id == result.badge_id
                    )
                )
                print(f"  - Revoked badge {result.badge_id} for user {result.user_id} ({deleted_badge.rowcount} row(s)).")
            
            # 2b. Revert XP
            if result.bonus_xp > 0:
                user = await session.scalar(select(User).where(User.id == result.user_id))
                if user:
                    old_xp = user.xp
                    user.xp = max(0, user.xp - result.bonus_xp)
                    
                    # Recalculate level
                    level = await session.scalar(
                        select(Level)
                        .where(Level.required_xp <= user.xp)
                        .order_by(Level.required_xp.desc())
                        .limit(1)
                    )
                    if level is not None and user.level_id != level.id:
                        user.level_id = level.id
                    
                    print(f"  - Revoked {result.bonus_xp} XP for user {result.user_id} (XP: {old_xp} -> {user.xp}, Level: {user.level_id}).")
                
                # Delete XpTransaction
                deleted_xp_tx = await session.execute(
                    delete(XpTransaction).where(
                        XpTransaction.user_id == result.user_id,
                        XpTransaction.amount == result.bonus_xp,
                        XpTransaction.source == XpSource.EVENT_REWARD
                    )
                )
                print(f"  - Deleted XP transaction ({deleted_xp_tx.rowcount} row(s)).")

        # 3. Clean up related tables in reverse dependency order (Bottom-up deletion)
        if post_ids:
            # Delete comments
            deleted_comments = await session.execute(
                delete(Comment).where(Comment.post_id.in_(post_ids))
            )
            print(f"Deleted {deleted_comments.rowcount} comments.")

            # Delete likes
            deleted_likes = await session.execute(
                delete(Like).where(Like.post_id.in_(post_ids))
            )
            print(f"Deleted {deleted_likes.rowcount} likes.")

            # Delete posts
            deleted_posts = await session.execute(
                delete(Post).where(Post.id.in_(post_ids))
            )
            print(f"Deleted {deleted_posts.rowcount} posts.")

        if submission_ids:
            # Delete XP transactions referencing these submissions to avoid ForeignKeyViolationError
            deleted_submission_xp_tx = await session.execute(
                delete(XpTransaction).where(XpTransaction.submission_id.in_(submission_ids))
            )
            print(f"Deleted {deleted_submission_xp_tx.rowcount} XP transaction(s) referencing submissions.")

            # Delete submissions
            deleted_submissions = await session.execute(
                delete(Submission).where(Submission.id.in_(submission_ids))
            )
            print(f"Deleted {deleted_submissions.rowcount} submissions.")

        if user_quest_ids:
            # Delete user_quests
            deleted_uq = await session.execute(
                delete(UserQuest).where(UserQuest.id.in_(user_quest_ids))
            )
            print(f"Deleted {deleted_uq.rowcount} user_quests.")

        # Delete EventResult
        deleted_results = await session.execute(
            delete(EventResult).where(EventResult.event_id == event.id)
        )
        print(f"Deleted {deleted_results.rowcount} event result rows.")

        # 4. Turn status to ACTIVE and extend by 1 day
        event.status = EventStatus.ACTIVE
        event.end_at = datetime.now(timezone.utc) + timedelta(days=1)
        
        await session.commit()
        print(f"Event reset successfully! Status set to ACTIVE. New end time: {event.end_at}")

if __name__ == "__main__":
    asyncio.run(main())
