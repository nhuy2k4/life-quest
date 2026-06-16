import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.submission import Submission
from app.models.user_quest import UserQuest
from app.services.user.user_service import UserService

async def inspect():
    async with AsyncSessionLocal() as session:
        # Get all users
        users = (await session.scalars(select(User))).all()
        print(f"Total users: {len(users)}")
        service = UserService(session)
        for u in users:
            await service._update_streak_if_needed(u)
            print(f"User: {u.username} (ID: {u.id}) - level: {u.level_id}, xp: {u.xp}, streak: {u.streak_days}")
            # Get submissions
            subs = (await session.scalars(
                select(Submission)
                .join(UserQuest, Submission.user_quest_id == UserQuest.id)
                .where(UserQuest.user_id == u.id)
            )).all()
            print(f"  Submissions ({len(subs)}):")
            for s in subs:
                print(f"    - ID: {s.id}, status: {s.status}, created_at: {s.created_at}")

if __name__ == "__main__":
    asyncio.run(inspect())
