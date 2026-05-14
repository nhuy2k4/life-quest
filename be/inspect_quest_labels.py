import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.quest import Quest

async def inspect_coffee_quest():
    async with AsyncSessionLocal() as session:
        stmt = select(Quest).where(Quest.title.ilike('%Coffee%'))
        result = await session.execute(stmt)
        q = result.scalars().first()
        if not q:
            print("Quest not found.")
            return
            
        print(f"\n--- Quest: {q.title} ---")
        print(f"Labels List: {q.labels}")
        print(f"Label Rules: {q.label_rules}")
        print(f"Min Confidence: {q.min_confidence}")

if __name__ == "__main__":
    asyncio.run(inspect_coffee_quest())
