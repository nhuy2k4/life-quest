import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.social import Post

async def main():
    async with AsyncSessionLocal() as session:
        post = await session.scalar(select(Post).where(Post.id == "79345f09-6aa6-47e0-851d-478c25fb72f7"))
        if post:
            print(f"Post ID: {post.id}")
            print(f"  event_id: {post.event_id}")
            print(f"  visibility: {post.visibility}")
        else:
            print("Post not found.")

if __name__ == "__main__":
    asyncio.run(main())
