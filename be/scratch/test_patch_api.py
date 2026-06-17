import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.social import Post
from app.models.user import User
from app.core.security import create_access_token
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as session:
        # Find a post without event_id
        post = await session.scalar(select(Post).where(Post.event_id.is_(None)).limit(1))
        if not post:
            print("No non-event post found to test.")
            return

        owner = await session.scalar(select(User).where(User.id == post.user_id))
        if not owner:
            print("No owner found for post.")
            return

        # Generate access token for owner
        token = create_access_token(user_id=owner.id, role=owner.role)

        # We must use TestClient in a context or run sync requests
        client = TestClient(app)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: Update visibility to friends
        print(f"Sending PATCH request to /api/v1/social/posts/{post.id} with visibility='friends'")
        response = client.patch(
            f"/api/v1/social/posts/{post.id}",
            json={"visibility": "friends"},
            headers=headers
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response JSON (caption/id check): Status={response.status_code}")
        if response.status_code == 200:
            print(f"Post visibility updated to: {response.json().get('visibility')}")

        # Restore original visibility
        print("Restoring visibility to public...")
        response = client.patch(
            f"/api/v1/social/posts/{post.id}",
            json={"visibility": "public"},
            headers=headers
        )
        print(f"Status Code: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(main())
