import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionLocal
from app.models.social import Post
from app.models.submission import Submission
from app.models.user_quest import UserQuest
from app.services.social.social_service import SocialService

async def test_serialize():
    async with AsyncSessionLocal() as session:
        try:
            stmt = select(Post).options(
                selectinload(Post.user),
                selectinload(Post.submission).selectinload(Submission.user_quest).selectinload(UserQuest.quest)
            ).limit(5)
            result = await session.scalars(stmt)
            posts = result.all()
            
            if not posts:
                print("No posts to test serialize!")
                return
                
            for p in posts:
                # Call the internal conversion method
                print(f"Serializing post id: {p.id}")
                resp = SocialService._to_post_response(p, liked_by_me=False)
                print(f"Serialized json model: {resp.model_dump_json()}")
            print("Full serialization success!")
        except Exception as e:
            print(f"Serialize failed: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_serialize())
