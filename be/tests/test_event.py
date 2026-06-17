"""
Tests cho Event endpoints và validation - LifeQuest Backend
Chạy: pytest tests/test_event.py -v
"""
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_event.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")

from app.core.config import settings
from app.core.database import Base
from app.deps.db import get_db
from app.main import app
from app.models.enums import UserRole
from app.models.quest import Quest
from app.models.user import User
from app.models.event import Event


@pytest_asyncio.fixture
async def client(tmp_path):
    test_db_path = tmp_path / "test_event.db"
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
async def test_event_update_constraints(client: AsyncClient):
    # Register & login admin
    await _register_user(client, username="admin", email="admin@example.com", password="SecurePass1")
    await _verify_and_promote("admin@example.com", UserRole.ADMIN)
    tokens = await _login(client, username="admin", password="SecurePass1")
    token = tokens["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create two quests to assign to events
    async with app.state.test_sessionmaker() as session:
        q1 = Quest(
            title="Quest 1",
            description="Test 1",
            template="Test 1",
            labels=["test"],
            min_confidence=0.5,
            xp_reward=10,
            is_active=True,
        )
        q2 = Quest(
            title="Quest 2",
            description="Test 2",
            template="Test 2",
            labels=["test"],
            min_confidence=0.5,
            xp_reward=10,
            is_active=True,
        )
        session.add_all([q1, q2])
        await session.commit()
        q1_id = q1.id
        q2_id = q2.id

    # --- Scenario 1: Event has not started ---
    future_start = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    future_end = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    
    # Create Event without location
    create_res = await client.post(
        "/api/v1/events",
        json={
            "title": "Future Event",
            "description": "Event in the future",
            "banner_url": "http://example.com/banner.png",
            "start_at": future_start,
            "end_at": future_end,
            "quest_ids": [str(q1_id)],
            "reward_config": [],
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    evt1 = create_res.json()
    evt1_id = evt1["id"]

    # Since it hasn't started, updating start_at, quest, and location should succeed
    new_start = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
    update_res = await client.patch(
        f"/api/v1/events/{evt1_id}",
        json={
            "start_at": new_start,
            "quest_ids": [str(q2_id)],
            "location_name": "New Loc",
            "latitude": 16.0,
            "longitude": 108.0,
            "radius_m": 500.0,
        },
        headers=headers,
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["location_name"] == "New Loc"
    assert len(updated["quests"]) == 1
    assert updated["quests"][0]["id"] == str(q2_id)

    # --- Scenario 2: Event has already started ---
    past_start = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    future_end_2 = (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat()

    # Create Event that is already active/started, and has NO location
    create_res_started_no_loc = await client.post(
        "/api/v1/events",
        json={
            "title": "Started Event No Loc",
            "description": "Started event",
            "banner_url": "http://example.com/banner.png",
            "start_at": past_start,
            "end_at": future_end_2,
            "quest_ids": [str(q1_id)],
            "reward_config": [],
        },
        headers=headers,
    )
    assert create_res_started_no_loc.status_code == 201
    evt2 = create_res_started_no_loc.json()
    evt2_id = evt2["id"]

    # Try to change start_at on started event -> should fail
    update_fail_start = await client.patch(
        f"/api/v1/events/{evt2_id}",
        json={"start_at": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()},
        headers=headers,
    )
    assert update_fail_start.status_code == 400
    assert "Không thể chỉnh sửa thời gian bắt đầu" in update_fail_start.json()["detail"]

    # Try to change quest on started event -> should fail
    update_fail_quest = await client.patch(
        f"/api/v1/events/{evt2_id}",
        json={"quest_ids": [str(q2_id)]},
        headers=headers,
    )
    assert update_fail_quest.status_code == 400
    assert "Không thể thay đổi nhiệm vụ" in update_fail_quest.json()["detail"]

    # Try to add a location on started event (where it wasn't attached originally) -> should fail
    update_fail_loc = await client.patch(
        f"/api/v1/events/{evt2_id}",
        json={
            "location_name": "Some Loc",
            "latitude": 16.0,
            "longitude": 108.0,
            "radius_m": 500.0,
        },
        headers=headers,
    )
    assert update_fail_loc.status_code == 400
    assert "Không thể chọn địa điểm cho sự kiện đã diễn ra nếu ban đầu không gắn địa điểm" in update_fail_loc.json()["detail"]

    # --- Scenario 3: Started Event WITH location ---
    # Create Event that is already active/started, and HAS a location
    create_res_started_with_loc = await client.post(
        "/api/v1/events",
        json={
            "title": "Started Event With Loc",
            "description": "Started event with loc",
            "banner_url": "http://example.com/banner.png",
            "start_at": past_start,
            "end_at": future_end_2,
            "quest_ids": [str(q1_id)],
            "reward_config": [],
            "location_name": "Initial Loc",
            "latitude": 16.06,
            "longitude": 108.20,
            "radius_m": 200.0,
        },
        headers=headers,
    )
    assert create_res_started_with_loc.status_code == 201
    evt3 = create_res_started_with_loc.json()
    evt3_id = evt3["id"]

    # Try to adjust location parameters on started event -> should succeed because it was already attached
    update_loc_ok = await client.patch(
        f"/api/v1/events/{evt3_id}",
        json={
            "location_name": "Adjusted Loc",
            "latitude": 16.07,
            "longitude": 108.21,
            "radius_m": 300.0,
        },
        headers=headers,
    )
    assert update_loc_ok.status_code == 200
    updated_evt3 = update_loc_ok.json()
    assert updated_evt3["location_name"] == "Adjusted Loc"
    assert updated_evt3["latitude"] == 16.07
    assert updated_evt3["radius_m"] == 300.0


@pytest.mark.asyncio
async def test_event_visibility_for_non_admins(client: AsyncClient):
    # Register admin & user
    await _register_user(client, username="admin_vis", email="admin_vis@example.com", password="SecurePass1")
    await _verify_and_promote("admin_vis@example.com", UserRole.ADMIN)
    admin_tokens = await _login(client, username="admin_vis", password="SecurePass1")
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}

    await _register_user(client, username="user_vis", email="user_vis@example.com", password="SecurePass1")
    await _verify_and_promote("user_vis@example.com", UserRole.USER)
    user_tokens = await _login(client, username="user_vis", password="SecurePass1")
    user_headers = {"Authorization": f"Bearer {user_tokens['access_token']}"}

    # Create one quest
    async with app.state.test_sessionmaker() as session:
        q1 = Quest(
            title="Quest 1",
            description="Test 1",
            template="Test 1",
            labels=["test"],
            min_confidence=0.5,
            xp_reward=10,
            is_active=True,
        )
        session.add(q1)
        await session.commit()
        q1_id = q1.id

    # Create 3 events:
    # 1. Draft event
    # 2. Future (upcoming) event (active status, but start_at in future)
    # 3. Ongoing event (active status, start_at in past, end_at in future)
    
    future_start = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    future_end = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    past_start = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    
    # 1. Draft
    await client.post(
        "/api/v1/events",
        json={
            "title": "Draft Event",
            "description": "draft",
            "banner_url": "http://example.com/banner.png",
            "start_at": past_start,
            "end_at": future_end,
            "status": "draft",
            "quest_ids": [str(q1_id)],
            "reward_config": [],
        },
        headers=admin_headers,
    )
    
    # 2. Future Active
    await client.post(
        "/api/v1/events",
        json={
            "title": "Future Event",
            "description": "future",
            "banner_url": "http://example.com/banner.png",
            "start_at": future_start,
            "end_at": future_end,
            "status": "active",
            "quest_ids": [str(q1_id)],
            "reward_config": [],
        },
        headers=admin_headers,
    )
    
    # 3. Ongoing Active
    await client.post(
        "/api/v1/events",
        json={
            "title": "Ongoing Event",
            "description": "ongoing",
            "banner_url": "http://example.com/banner.png",
            "start_at": past_start,
            "end_at": future_end,
            "status": "active",
            "quest_ids": [str(q1_id)],
            "reward_config": [],
        },
        headers=admin_headers,
    )

    # Admin lists events (without status filter) -> should see all 3 events
    admin_list = await client.get("/api/v1/events", headers=admin_headers)
    assert admin_list.status_code == 200
    admin_titles = [e["title"] for e in admin_list.json()]
    assert "Draft Event" in admin_titles
    assert "Future Event" in admin_titles
    assert "Ongoing Event" in admin_titles

    # User lists events (without status filter) -> should only see "Ongoing Event" (no drafts, no future events)
    user_list = await client.get("/api/v1/events", headers=user_headers)
    assert user_list.status_code == 200
    user_titles = [e["title"] for e in user_list.json()]
    assert "Ongoing Event" in user_titles
    assert "Draft Event" not in user_titles
    assert "Future Event" not in user_titles

    # User queries with status=active -> should only see "Ongoing Event"
    user_list_active = await client.get("/api/v1/events?status=active", headers=user_headers)
    assert user_list_active.status_code == 200
    user_active_titles = [e["title"] for e in user_list_active.json()]
    assert "Ongoing Event" in user_active_titles
    assert "Draft Event" not in user_active_titles
    assert "Future Event" not in user_active_titles
