import asyncio
import uuid
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.social import Post

async def main():
    user_id = uuid.UUID("0a16211f-214b-4442-b1de-64f325b9fc3d")
    async with AsyncSessionLocal() as session:
        # Find the latest post by the user
        stmt = (
            select(Post)
            .where(Post.user_id == user_id)
            .order_by(Post.created_at.desc())
            .limit(1)
        )
        post = await session.scalar(stmt)
        if post is None:
            print("No posts found for this user.")
            return
            
        print("Found latest post:")
        print(f"Post ID: {post.id}")
        print(f"Caption: {post.caption}")
        print(f"Image URL: {post.image_url}")
        print(f"Created At: {post.created_at}")
        print(f"Event ID: {post.event_id}")
        print(f"Submission ID: {post.submission_id}")
        
        # Delete the post
        await session.delete(post)
        await session.commit()
        print("Post deleted successfully.")

if __name__ == "__main__":
    asyncio.run(main())
