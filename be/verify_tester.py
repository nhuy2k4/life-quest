import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User
from sqlalchemy import select

async def confirm():
    async with AsyncSessionLocal() as s:
        u = await s.scalar(select(User).where(User.username=='tester'))
        print(f"Row check result: {u.username if u else 'NOT_FOUND'}")

if __name__ == "__main__":
    asyncio.run(confirm())
