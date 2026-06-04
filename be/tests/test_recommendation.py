"""Recommendation & gamification API tests.

Chạy: pytest tests/test_recommendation.py -v
"""

import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.deps.auth import CurrentUser, get_current_user
from app.deps.db import get_db
from app.main import app
from app.models.enums import ActivityLevel, QuestDifficulty, XpSource
from app.models.poi import Poi
from app.models.quest import Category, Quest
from app.models.recommendation import RecommendationLog
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.user_quest import UserQuest
from app.models.xp_transaction import XpTransaction

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_recommendation.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
	bind=test_engine,
	class_=AsyncSession,
	expire_on_commit=False,
)


async def override_get_db():
	async with TestSessionLocal() as session:
		yield session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
	async with test_engine.begin() as conn:
		await conn.run_sync(Base.metadata.create_all)
	yield
	async with test_engine.begin() as conn:
		await conn.run_sync(Base.metadata.drop_all)
	await test_engine.dispose()


@pytest_asyncio.fixture
async def seeded_user_and_quests():
	async with TestSessionLocal() as session:
		user_id = uuid.uuid4()

		user = User(
			id=user_id,
			username=f"recommend_user_{user_id.hex[:6]}",
			email=f"{user_id.hex[:8]}@example.com",
			password_hash="hashed",
			provider="local",
			level_id=1,
			xp=20,
			streak_days=0,
			trust_score=1.0,
			role="user",
			is_verified=True,
			is_banned=False,
			onboarding_completed=True,
		)

		food = Category(name=f"Food-{user_id.hex[:4]}", icon="food")
		fitness = Category(name=f"Fitness-{user_id.hex[:4]}", icon="fit")

		quest_easy = Quest(
			id=uuid.uuid4(),
			title="Easy food quest",
			description="A",
			xp_reward=100,
			difficulty=QuestDifficulty.EASY,
			approval_rate=1.0,
			time_limit_hours=24,
			location_required=False,
			is_active=True,
			created_at=datetime.now(timezone.utc),
			updated_at=datetime.now(timezone.utc),
		)
		quest_easy.categories.append(food)

		quest_hard = Quest(
			id=uuid.uuid4(),
			title="Hard fitness quest",
			description="B",
			xp_reward=300,
			difficulty=QuestDifficulty.HARD,
			approval_rate=1.0,
			time_limit_hours=24,
			location_required=True,
			is_active=True,
			created_at=datetime.now(timezone.utc),
			updated_at=datetime.now(timezone.utc),
		)
		quest_hard.categories.append(fitness)

		session.add_all([user, food, fitness, quest_easy, quest_hard])
		await session.flush()

		preference = UserPreference(
			user_id=user_id,
			interests=[food.id],
			interest_weights={},
			activity_level=ActivityLevel.LOW,
			location_enabled=True,
			notification_enabled=True,
		)
		session.add(preference)
		await session.commit()

		return user_id


@pytest_asyncio.fixture
async def seeded_user_without_preferences():
	async with TestSessionLocal() as session:
		user_id = uuid.uuid4()
		user = User(
			id=user_id,
			username=f"no_pref_{user_id.hex[:6]}",
			email=f"no_pref_{user_id.hex[:8]}@example.com",
			password_hash="hashed",
			provider="local",
			level_id=1,
			xp=0,
			streak_days=0,
			trust_score=1.0,
			role="user",
			is_verified=True,
			is_banned=False,
			onboarding_completed=False,
		)

		quest = Quest(
			id=uuid.uuid4(),
			title="Fallback quest",
			description="fallback",
			xp_reward=80,
			difficulty=QuestDifficulty.EASY,
			approval_rate=1.0,
			time_limit_hours=24,
			location_required=False,
			is_active=True,
			created_at=datetime.now(timezone.utc),
			updated_at=datetime.now(timezone.utc),
		)

		session.add_all([user, quest])
		await session.commit()

		return user_id


def _build_client(user_id: uuid.UUID, onboarding_completed: bool = True):
	async def override_current_user():
		return CurrentUser(
			id=user_id,
			role="user",
			onboarding_completed=onboarding_completed,
			is_banned=False,
		)

	app.dependency_overrides[get_db] = override_get_db
	app.dependency_overrides[get_current_user] = override_current_user
	return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.mark.asyncio
async def test_recommendation_returns_items(seeded_user_and_quests):
	async with _build_client(seeded_user_and_quests, onboarding_completed=True) as client:
		response = await client.get("/api/v1/recommendations/quests", params={"page": 1, "page_size": 20})
		assert response.status_code == 200

		payload = response.json()
		assert "request_id" in payload
		assert payload["recommended_for_you"]
		assert payload["sections"]
		first = payload["recommended_for_you"][0]
		assert "final_score" in first
		assert "reasons" in first
		assert "score_breakdown" in first
		assert first["score_breakdown"]["interest"] >= 0
	app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_recommendation_fallback_without_preferences(seeded_user_without_preferences):
	async with _build_client(seeded_user_without_preferences, onboarding_completed=False) as client:
		response = await client.get("/api/v1/recommendations/quests")
		assert response.status_code == 200
		payload = response.json()
		assert payload["explore_new_things"] or payload["recommended_for_you"]
	app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_recommendation_log_endpoint(seeded_user_and_quests):
	async with _build_client(seeded_user_and_quests, onboarding_completed=True) as client:
		response = await client.get("/api/v1/recommendations/quests", params={"page": 1, "page_size": 5})
		assert response.status_code == 200
		payload = response.json()
		request_id = uuid.UUID(payload["request_id"])
		item = payload["recommended_for_you"][0]
		quest_id = item["id"]

		log_payload = {
			"request_id": str(request_id),
			"quest_id": quest_id,
			"event": "clicked",
			"section": "recommended_for_you",
			"rank": 1,
			"final_score": item["final_score"],
			"reasons": item["reasons"],
			"score_breakdown": item["score_breakdown"],
		}
		log_response = await client.post("/api/v1/recommendations/events", json=log_payload)
		assert log_response.status_code == 200

	async with TestSessionLocal() as session:
		rows = await session.execute(select(RecommendationLog).where(RecommendationLog.request_id == request_id))
		assert rows.scalars().first() is not None
	app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_recommendation_debug_nearby_and_continue(seeded_user_and_quests):
	async with TestSessionLocal() as session:
		poi = Poi(
			name="Demo Cafe",
			poi_type="cafe",
			latitude=10.0,
			longitude=10.0,
			radius_m=500,
			source="test",
			external_id=uuid.uuid4().hex[:8],
		)
		quest = Quest(
			id=uuid.uuid4(),
			title="Nearby cafe quest",
			description="nearby",
			xp_reward=90,
			difficulty=QuestDifficulty.EASY,
			approval_rate=1.0,
			time_limit_hours=24,
			location_required=True,
			poi_required=True,
			is_active=True,
			poi=poi,
			created_at=datetime.now(timezone.utc),
			updated_at=datetime.now(timezone.utc),
		)
		session.add_all([poi, quest])
		await session.flush()
		session.add(
			UserQuest(
				user_id=seeded_user_and_quests,
				quest_id=quest.id,
				status="started",
				started_at=datetime.now(timezone.utc),
			)
		)
		await session.commit()

	async with _build_client(seeded_user_and_quests, onboarding_completed=True) as client:
		response = await client.get(
			"/api/v1/recommendations/quests",
			params={"lat": 10.0, "lng": 10.0, "debug": "true"},
		)
		assert response.status_code == 200
		payload = response.json()
		continue_items = payload["continue_your_missions"]
		assert continue_items
		assert continue_items[0]["score_breakdown"]["continue"] == 35.0
		assert continue_items[0]["debug"] is not None
		nearby_items = payload["trending_near_you"]
		assert any(item["score_breakdown"]["nearby"] == 15.0 for item in nearby_items)
	app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_xp_history_returns_paginated_rows(seeded_user_and_quests):
	async with TestSessionLocal() as session:
		xp_1 = XpTransaction(
			user_id=seeded_user_and_quests,
			submission_id=None,
			amount=30,
			source=XpSource.QUEST_APPROVED,
		)
		xp_2 = XpTransaction(
			user_id=seeded_user_and_quests,
			submission_id=None,
			amount=50,
			source=XpSource.QUEST_APPROVED,
		)
		session.add_all([xp_1, xp_2])
		await session.commit()

	async with _build_client(seeded_user_and_quests, onboarding_completed=True) as client:
		response = await client.get("/api/v1/gamification/xp-history", params={"page": 1, "page_size": 1})
		assert response.status_code == 200

		payload = response.json()
		assert payload["page"] == 1
		assert payload["page_size"] == 1
		assert payload["total"] >= 2
		assert len(payload["items"]) == 1
		assert payload["items"][0]["source"] == "quest_approved"
	app.dependency_overrides.clear()
