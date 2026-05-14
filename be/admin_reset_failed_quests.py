import asyncio
from sqlalchemy import text, delete
from app.core.database import AsyncSessionLocal
from app.models.user_quest import UserQuest
from app.models.enums import UserQuestStatus

async def reset_failed_quests():
    async with AsyncSessionLocal() as session:
        print("[LOG] Scanning for User Quests stuck in REJECTED status...")
        
        from sqlalchemy import select, func
        count = await session.scalar(select(func.count()).select_from(UserQuest).where(UserQuest.status == UserQuestStatus.REJECTED))
        
        if count == 0:
            print("[SUCCESS] No failed quests found in database.")
            return
            
        print(f"[INFO] Found {count} failed quests. Deleting records for full reset...")
        await session.execute(delete(UserQuest).where(UserQuest.status == UserQuestStatus.REJECTED))
        await session.commit()
        print(f"[DONE] Success! {count} quest(s) reset to available.")

if __name__ == "__main__":
    asyncio.run(reset_failed_quests())
