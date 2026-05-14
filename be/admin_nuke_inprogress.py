import asyncio
from sqlalchemy import delete, or_
from app.core.database import AsyncSessionLocal
from app.models.user_quest import UserQuest
from app.models.enums import UserQuestStatus

async def nuke_inprogress_quests():
    async with AsyncSessionLocal() as session:
        print("[LOG] Identifying all in-progress/pending quests to reset completely...")
        
        # Target BOTH 'started' and 'submitted' statuses to ensure complete liberation
        stmt = delete(UserQuest).where(
            or_(
                UserQuest.status == UserQuestStatus.STARTED,
                UserQuest.status == UserQuestStatus.SUBMITTED,
                UserQuest.status == UserQuestStatus.REJECTED
            )
        )
        
        result = await session.execute(stmt)
        await session.commit()
        
        print(f"[SUCCESS] Deleted all incomplete quests from database to return them to recommendation pool.")

if __name__ == "__main__":
    asyncio.run(nuke_inprogress_quests())
