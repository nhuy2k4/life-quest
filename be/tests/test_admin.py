"""
Tests cho Admin endpoints — LifeQuest Backend

Chạy: pytest tests/test_admin.py -v
"""
import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_admin.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

from app.core.config import settings
from app.core.database import Base
from app.deps.db import get_db
from app.main import app
from app.models.enums import UserRole
from app.models.quest import Quest
from app.models.user import User


@pytest_asyncio.fixture
async def client(tmp_path):
    test_db_path = tmp_path / "test_admin.db"
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


async def _verify_and_promote(email: str, role: UserRole) -> None:
    async with app.state.test_sessionmaker() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        user.is_verified = True
        user.role = role
        await session.commit()


async def _login(client: AsyncClient, *, username: str, password: str) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()


@pytest.mark.asyncio
async def test_admin_user_ban_and_xp_adjust(client: AsyncClient):
    await _register_user(client, username="admin", email="admin@example.com", password="SecurePass1")
    await _register_user(client, username="user", email="user@example.com", password="SecurePass1")

    await _verify_and_promote("admin@example.com", UserRole.ADMIN)
    await _verify_and_promote("user@example.com", UserRole.USER)

    tokens = await _login(client, username="admin", password="SecurePass1")
    access_token = tokens["access_token"]

    async with app.state.test_sessionmaker() as session:
        result = await session.execute(select(User).where(User.email == "user@example.com"))
        target = result.scalar_one()

    response = await client.patch(
        f"/api/v1/admin/users/{target.id}/ban",
        json={"is_banned": True},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200

    adjust = await client.post(
        f"/api/v1/admin/users/{target.id}/xp-adjust",
        json={"amount": 50, "reason": "manual"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert adjust.status_code == 200
    assert adjust.json()["new_xp"] == 50


@pytest.mark.asyncio
async def test_admin_list_quests(client: AsyncClient):
    await _register_user(client, username="admin2", email="admin2@example.com", password="SecurePass1")
    await _verify_and_promote("admin2@example.com", UserRole.ADMIN)

    tokens = await _login(client, username="admin2", password="SecurePass1")
    access_token = tokens["access_token"]

    async with app.state.test_sessionmaker() as session:
        quest = Quest(
            title="Quest",
            description="Test",
            template="Test",
            labels=["test"],
            min_confidence=0.5,
            xp_reward=10,
            is_active=True,
        )
        session.add(quest)
        await session.commit()

    response = await client.get(
        "/api/v1/admin/quests",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] >= 1
