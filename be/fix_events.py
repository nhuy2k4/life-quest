import asyncio
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.social import Post
from app.models.event import EventQuest

async def main():
    async with AsyncSessionLocal() as session:
        # Find all posts with a quest_id but no event_id
        result = await session.execute(
            select(Post, EventQuest.event_id)
            .join(EventQuest, EventQuest.quest_id == Post.quest_id)
            .where(Post.event_id == None)
        )
        rows = result.all()
        updated = 0
        for post, event_id in rows:
            post.event_id = event_id
            updated += 1
            
        if updated > 0:
            await session.commit()
            print(f"Fixed {updated} posts to link to their event.")
        else:
            print("No posts needed fixing.")

if __name__ == "__main__":
    asyncio.run(main())
