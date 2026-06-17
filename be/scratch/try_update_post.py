import asyncio
import uuid
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.social import Post
from app.models.enums import PostVisibility

async def main():
    async with AsyncSessionLocal() as session:
        # Find any post
        post = await session.scalar(select(Post).limit(1))
        if post is None:
            print("No posts found in database to test.")
            return

        print(f"Testing update on Post ID: {post.id} (Current visibility: {post.visibility})")
        original_visibility = post.visibility
        try:
            # Try setting to friends
            post.visibility = PostVisibility.FRIENDS
            print("Set visibility to FRIENDS. Committing...")
            await session.commit()
            print("Commit successful!")

            # Restore original
            post.visibility = original_visibility
            await session.commit()
            print("Restored original visibility successfully!")
        except Exception as e:
            print(f"Error during commit: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(main())
