import asyncio
from sqlalchemy import select, or_, and_
from app.core.database import AsyncSessionLocal
from app.models.social import Post, Follow
from app.models.enums import PostVisibility

async def main():
    async with AsyncSessionLocal() as session:
        # 1. Print all posts and their visibility
        posts = (await session.scalars(select(Post))).all()
        print(f"\n--- Total Posts in database: {len(posts)} ---")
        for p in posts:
            print(f"Post ID: {p.id}")
            print(f"  User ID: {p.user_id}")
            print(f"  Visibility: {p.visibility} (type: {type(p.visibility)})")
            print(f"  Caption: {p.caption}")
            print(f"  Event ID: {p.event_id}")
            print("-" * 40)

        # 2. Check follow records
        follows = (await session.scalars(select(Follow))).all()
        print(f"\n--- Total Follows: {len(follows)} ---")
        for f in follows:
            print(f"Follower {f.follower_id} -> Following {f.following_id}")
            print("-" * 40)

        # 3. Simulate feed query for each user
        users = list(set([p.user_id for p in posts]))
        if not users:
            print("No users found.")
            return

        for viewer_id in users:
            print(f"\n--- Feed for viewer {viewer_id} ---")
            friends_subquery = select(Follow.following_id).where(
                Follow.follower_id == viewer_id,
                Follow.following_id.in_(
                    select(Follow.follower_id).where(Follow.following_id == viewer_id)
                )
            )
            visibility_filter = or_(
                Post.visibility == PostVisibility.PUBLIC,
                and_(
                    Post.visibility == PostVisibility.FRIENDS,
                    or_(Post.user_id.in_(friends_subquery), Post.user_id == viewer_id)
                ),
                and_(Post.visibility == PostVisibility.PRIVATE, Post.user_id == viewer_id),
            )
            stmt = select(Post).where(visibility_filter)
            visible_posts = (await session.scalars(stmt)).all()
            for p in visible_posts:
                print(f"  - Post {p.id} (Owner: {p.user_id}, Visibility: {p.visibility})")

if __name__ == "__main__":
    asyncio.run(main())
