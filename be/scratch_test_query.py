import asyncio
import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionLocal
from app.models.social import Post
from app.models.submission import Submission
from app.models.user_quest import UserQuest

async def test_query():
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(Post).options(
                selectinload(Post.user),
                selectinload(Post.submission).selectinload(Submission.user_quest).selectinload(UserQuest.quest)
            ).limit(1)
            result = await session.execute(stmt)
            print("Query success!")
        except Exception as e:
            print(f"Query failed: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_query())
