import asyncio
import uuid
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password
from app.services.recommendation.recommendation_service import RecommendationService
from sqlalchemy import select

async def test_with_real_user():
    async with AsyncSessionLocal() as session:
        try:
            # 1. Create a mock user to simulate fresh registration
            unique_username = f"tester_{uuid.uuid4().hex[:8]}"
            user = User(
                id=uuid.uuid4(),
                username=unique_username,
                email=f"{unique_username}@lifequest.local",
                password_hash=hash_password("password123"),
                level_id=1,
                onboarding_completed=False
            )
            session.add(user)
            await session.commit()
            print(f"Created user '{user.username}' with ID: {user.id}")
            
            # 2. Execute recommendation engine
            service = RecommendationService(session)
            result = await service.get_recommended_quests(
                user_id=user.id,
                onboarding_completed=user.onboarding_completed,
                page=1,
                page_size=10
            )
            
            print(f"--- RESULTS FOR NEW USER ---")
            print(f"Total items returned: {len(result.items)}")
            
            # 3. Clean up user afterwards to keep DB clean
            await session.delete(user)
            await session.commit()
            print("Cleaned up test user.")
        except Exception as e:
            with open("CRASH_ERROR.txt", "w", encoding="utf-8") as f:
                import traceback
                f.write(traceback.format_exc())
            print("ERROR WRITTEN TO CRASH_ERROR.txt")

if __name__ == "__main__":
    asyncio.run(test_with_real_user())
