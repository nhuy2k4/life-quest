import asyncio
import uuid
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.services.recommendation.recommendation_service import RecommendationService
from sqlalchemy import select

async def debug_recommendations():
    async with AsyncSessionLocal() as session:
        # Find the new test user created by the user manually or just get first one
        user = await session.scalar(select(User).order_by(User.created_at.desc()).limit(1))
        if not user:
            print("NO USERS in database yet! Need to register first.")
            return
        
        print(f"Debugging recommendations for User ID: {user.id}, username: {user.username}")
        service = RecommendationService(session)
        
        # Simulate request
        result = await service.get_recommended_quests(
            user_id=user.id,
            onboarding_completed=user.onboarding_completed,
            page=1,
            page_size=10
        )
        
        print(f"Total items returned: {len(result.items)}")
        for i, item in enumerate(result.items):
            print(f"[{i+1}] Quest: {item.id} - Score: {item.recommendation_score}")

if __name__ == "__main__":
    asyncio.run(debug_recommendations())
