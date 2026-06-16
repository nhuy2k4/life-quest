import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.event import Event, EventQuest
from app.models.social import Post

async def main():
    async with AsyncSessionLocal() as session:
        events = (await session.scalars(select(Event))).all()
        print(f"Total events in database: {len(events)}")
        for e in events:
            print(f"Event: {e.title} (ID: {e.id}, Status: {e.status}, End At: {e.end_at})")
            quests = (await session.scalars(select(EventQuest).where(EventQuest.event_id == e.id))).all()
            print(f"  Quests linked: {[q.quest_id for q in quests]}")
        
        posts = (await session.scalars(select(Post))).all()
        print(f"\nTotal posts in database: {len(posts)}")
        for p in posts:
            print(f"Post ID: {p.id}, Event ID: {p.event_id}, Quest ID: {p.quest_id}, Caption: {p.caption}")

if __name__ == "__main__":
    asyncio.run(main())
