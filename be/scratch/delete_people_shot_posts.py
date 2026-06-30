import asyncio
import uuid
from sqlalchemy import select, or_
from app.core.database import AsyncSessionLocal
from app.models.social import Post
from app.models.submission import Submission
from app.models.user_quest import UserQuest

async def main():
    quest_id = uuid.UUID("a65f6494-33a0-413b-9f67-c89306f2b08d")
    async with AsyncSessionLocal() as session:
        # Find all submissions linked to this quest
        sub_stmt = select(Submission.id).join(UserQuest, UserQuest.id == Submission.user_quest_id).where(UserQuest.quest_id == quest_id)
        sub_ids = (await session.scalars(sub_stmt)).all()
        
        # Query posts directly linked to the quest_id or linked to those submissions
        stmt = select(Post).where(
            or_(
                Post.quest_id == quest_id,
                Post.submission_id.in_(sub_ids) if sub_ids else False
            )
        )
        posts = (await session.scalars(stmt)).all()
        
        if not posts:
            print("No posts found related to the 'People shot' quest.")
            return
            
        print(f"Found {len(posts)} posts to delete:")
        for idx, post in enumerate(posts):
            print(f"{idx+1}. Post ID: {post.id} | User ID: {post.user_id} | Created At: {post.created_at} | Image: {post.image_url}")
            
        # Delete the posts
        for post in posts:
            await session.delete(post)
            
        await session.commit()
        print("All related posts deleted successfully.")

if __name__ == "__main__":
    asyncio.run(main())
