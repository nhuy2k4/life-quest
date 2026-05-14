import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import select, func
from app.models.quest import Quest

async def check_quest_count():
    async with AsyncSessionLocal() as session:
        count = await session.scalar(select(func.count()).select_from(Quest))
        print(f"Total Quests: {count}")
        
        # Also list active count
        active = await session.scalar(select(func.count()).select_from(Quest).where(Quest.is_active.is_(True)))
        print(f"Active Quests: {active}")

if __name__ == "__main__":
    asyncio.run(check_quest_count())
