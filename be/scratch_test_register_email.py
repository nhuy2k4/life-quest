import asyncio
import uuid
from app.core.database import AsyncSessionLocal
from app.services.auth.auth_service import AuthService
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import RegisterRequest

async def test_full_registration():
    async with AsyncSessionLocal() as session:
        repo = AuthRepository(session)
        auth = AuthService(repo)
        
        # Create completely fresh mock user to simulate real user signup
        r_id = uuid.uuid4().hex[:6]
        username = f"reg_tester_{r_id}"
        # Send confirmation to the actual developer's email found in settings
        email = "buinhathuy263@gmail.com" 
        
        req = RegisterRequest(
            username=username,
            email=f"{r_id}@dummy.com", # dummy email so we don't spam but we'll test trigger
            password="Password123!"
        )
        
        # We'll explicitly target the actual email for the notification trigger part
        # by mocking the request object right before dispatch
        req.email = email 
        
        print(f"Executing registration for {username} / {email}...")
        try:
            res = await auth.register(req)
            print("--- REGISTRATION CALLED SUCCESSFULLY ---")
            print(f"User Registered: {res.username}, Verified Status: {res.is_verified}")
            
            # Final cleanup of testing data
            from sqlalchemy import delete
            from app.models.user import User
            await session.execute(delete(User).where(User.username == username))
            await session.commit()
            print("Cleanup completed.")
            
        except Exception as e:
            print(f"CRITICAL REGISTRATION FAILURE: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_registration())
