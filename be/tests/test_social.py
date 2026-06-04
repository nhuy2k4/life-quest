"""
Tests cho Social endpoints — LifeQuest Backend

Chạy: pytest tests/test_social.py -v
"""
import os
import sys
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_social.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

from app.core.config import settings
from app.core.database import Base
from app.deps.db import get_db
from app.main import app
from app.models.quest import Quest
from app.models.recommendation import RecommendationLog
from app.models.submission import Submission
from app.models.user import User
from app.models.user_quest import UserQuest


@pytest_asyncio.fixture
async def client(tmp_path):
    test_db_path = tmp_path / "test_social.db"
    test_db_url = f"sqlite+aiosqlite:///{test_db_path}"

    test_engine = create_async_engine(test_db_url, echo=False)
    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    settings.TESTING = True
    settings.EMAIL_SENDING_ENABLED = False

    app.dependency_overrides[get_db] = override_get_db
    app.state.test_sessionmaker = TestSessionLocal

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    settings.TESTING = False
    settings.EMAIL_SENDING_ENABLED = True
    app.state.test_sessionmaker = None
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


async def _register_user(client: AsyncClient, *, username: str, email: str, password: str) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()


async def _verify_user(email: str) -> None:
    async with app.state.test_sessionmaker() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.is_verified = True
        await session.commit()


async def _login(client: AsyncClient, *, username: str, password: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()


async def _create_submission(user_id: uuid.UUID) -> Submission:
    async with app.state.test_sessionmaker() as session:
        quest = Quest(
            title="Quest 1",
            description="Test",
            template="Test",
            labels=["test"],
            min_confidence=0.5,
            xp_reward=50,
            is_active=True,
        )
        session.add(quest)
        await session.flush()

        user_quest = UserQuest(
            user_id=user_id,
            quest_id=quest.id,
        )
        session.add(user_quest)
        await session.flush()

        submission = Submission(
            user_quest_id=user_quest.id,
            image_url="https://example.com/image.jpg",
            cloudinary_public_id="cid",
            file_hash="a" * 32,
        )
        session.add(submission)
        await session.commit()
        await session.refresh(submission)
        return submission


@pytest.mark.asyncio
async def test_follow_and_feed(client: AsyncClient):
    await _register_user(client, username="user1", email="user1@example.com", password="SecurePass1")
    await _register_user(client, username="user2", email="user2@example.com", password="SecurePass1")
    await _verify_user("user1@example.com")
    await _verify_user("user2@example.com")

    tokens = await _login(client, username="user1", password="SecurePass1")
    access_token = tokens["access_token"]

    async with app.state.test_sessionmaker() as session:
        result = await session.execute(select(User).where(User.email == "user2@example.com"))
        user2 = result.scalar_one()

    response = await client.post(
        f"/api/v1/social/users/{user2.id}/follow",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200

    profile = await client.get(
        f"/api/v1/users/{user2.id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert profile.status_code == 200
    assert profile.json()["data"]["is_following"] is True
    assert profile.json()["data"]["stats"]["followers"] == 1

    feed = await client.get(
        "/api/v1/social/feed",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert feed.status_code == 200
    assert feed.json()["items"] == []


@pytest.mark.asyncio
async def test_post_like_comment_flow(client: AsyncClient):
    await _register_user(client, username="user3", email="user3@example.com", password="SecurePass1")
    await _verify_user("user3@example.com")

    tokens = await _login(client, username="user3", password="SecurePass1")
    access_token = tokens["access_token"]

    async with app.state.test_sessionmaker() as session:
        result = await session.execute(select(User).where(User.email == "user3@example.com"))
        user = result.scalar_one()

    submission = await _create_submission(user.id)
    expected_quest_id = submission.user_quest_id

    post = await client.post(
        "/api/v1/social/posts",
        json={"submission_id": str(submission.id)},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert post.status_code == 200
    post_id = post.json()["id"]

    like = await client.post(
        f"/api/v1/social/posts/{post_id}/like",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert like.status_code == 200

    comment = await client.post(
        f"/api/v1/social/posts/{post_id}/comments",
        json={"content": "Nice"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert comment.status_code == 200

    comments = await client.get(
        f"/api/v1/social/posts/{post_id}/comments",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert comments.status_code == 200
    assert comments.json()["total"] == 1

    async with app.state.test_sessionmaker() as session:
        log_rows = await session.execute(
            select(
                RecommendationLog.event,
                RecommendationLog.post_id,
                RecommendationLog.quest_id,
                RecommendationLog.score,
            )
            .where(RecommendationLog.post_id == uuid.UUID(post_id))
            .order_by(RecommendationLog.created_at.asc())
        )
        logs = log_rows.all()
        assert [event for event, *_ in logs] == ["post_liked", "post_commented"]
        assert all(log_post_id == uuid.UUID(post_id) for _, log_post_id, *_ in logs)
        quest_rows = await session.execute(select(UserQuest.quest_id).where(UserQuest.id == expected_quest_id))
        expected_quest_id = quest_rows.scalar_one()
        assert all(log_quest_id == expected_quest_id for _, _, log_quest_id, *_ in logs)
        assert [score for *_, score in logs] == [1.0, 3.0]


@pytest.mark.asyncio
async def test_create_post_with_same_submission_is_idempotent(client: AsyncClient):
    await _register_user(client, username="user4", email="user4@example.com", password="SecurePass1")
    await _verify_user("user4@example.com")

    tokens = await _login(client, username="user4", password="SecurePass1")
    access_token = tokens["access_token"]

    async with app.state.test_sessionmaker() as session:
        result = await session.execute(select(User).where(User.email == "user4@example.com"))
        user = result.scalar_one()

    submission = await _create_submission(user.id)
    payload = {"submission_id": str(submission.id), "caption": "same submit"}

    first = await client.post(
        "/api/v1/social/posts",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    second = await client.post(
        "/api/v1/social/posts",
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
