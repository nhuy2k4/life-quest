import asyncio
import uuid
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password
from sqlalchemy import select

async def create_permanent_test_account():
    async with AsyncSessionLocal() as session:
        username = "tester"
        password = "password123"
        email = "tester@lifequest.local"
        
        # Clear conflicts aggressively
        from sqlalchemy import delete
        await session.execute(delete(User).where((User.username == username) | (User.email == email)))
        await session.commit()
        print("Cleared existing conflicting rows.")

        user = User(
            id=uuid.uuid4(),
            username=username,
            email=email,
            password_hash=hash_password(password),
            level_id=1,
            onboarding_completed=True, # Set this to true so recommended quests flow naturally
            is_verified=True
        )
        session.add(user)
        await session.commit()
        print(f"✅ Successfully CREATED permanent test account!")
        print(f"User: {username}")
        print(f"Pass: {password}")

if __name__ == "__main__":
    asyncio.run(create_permanent_test_account())
