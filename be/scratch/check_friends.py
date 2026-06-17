import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.social import Follow
from app.models.user import User

async def main():
    async with AsyncSessionLocal() as session:
        follows = (await session.scalars(select(Follow))).all()
        print(f"Total follows: {len(follows)}")
        for f in follows:
            follower = await session.scalar(select(User.username).where(User.id == f.follower_id))
            following = await session.scalar(select(User.username).where(User.id == f.following_id))
            print(f"{follower} ({f.follower_id}) -> {following} ({f.following_id})")

if __name__ == "__main__":
    asyncio.run(main())
