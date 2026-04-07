"""Quest API tests.

Chạy: pytest tests/test_quest.py -v
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
from app.models.enums import SubmissionStatus, UserQuestStatus
from app.models.quest import Quest
from app.models.submission import Submission
from app.models.user import User
from app.models.user_quest import UserQuest
from app.models.xp_transaction import XpTransaction
from app.repositories.submission_repository import SubmissionRepository
from app.services.gamification.xp_service import XpService

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_quest.db"


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
async def seeded_user_and_quest():
    async with TestSessionLocal() as session:
        user_id = uuid.uuid4()
        quest_id = uuid.uuid4()

        user = User(
            id=user_id,
            username=f"quest_user_{user_id.hex[:6]}",
            email=f"{user_id.hex[:8]}@example.com",
            password_hash="hashed",
            provider="local",
            level_id=1,
            xp=0,
            streak_days=0,
            trust_score=1.0,
            role="user",
            is_verified=True,
            is_banned=False,
            onboarding_completed=True,
        )
        quest = Quest(
            id=quest_id,
            title="Quest test",
            description="Quest test description",
            xp_reward=100,
            difficulty="easy",
            approval_rate=1.0,
            time_limit_hours=24,
            location_required=False,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        session.add(user)
        session.add(quest)
        await session.commit()

        return user_id, quest_id


@pytest_asyncio.fixture
async def client(seeded_user_and_quest):
    user_id, _ = seeded_user_and_quest

    async def override_current_user():
        return CurrentUser(
            id=user_id,
            role="user",
            onboarding_completed=True,
            is_banned=False,
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_client(seeded_user_and_quest):
    user_id, _ = seeded_user_and_quest

    async def override_current_user_admin():
        return CurrentUser(
            id=user_id,
            role="admin",
            onboarding_completed=True,
            is_banned=False,
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user_admin

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_quests_success(client: AsyncClient):
    response = await client.get("/api/v1/quests")
    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert payload["total"] >= 1


@pytest.mark.asyncio
async def test_start_quest_success(client: AsyncClient, seeded_user_and_quest):
    _, quest_id = seeded_user_and_quest

    response = await client.post(f"/api/v1/quests/{quest_id}/start")
    assert response.status_code == 201
    data = response.json()
    assert data["quest_id"] == str(quest_id)
    assert data["status"] == "started"


@pytest.mark.asyncio
async def test_start_quest_duplicate(client: AsyncClient, seeded_user_and_quest):
    _, quest_id = seeded_user_and_quest

    first = await client.post(f"/api/v1/quests/{quest_id}/start")
    assert first.status_code == 201

    second = await client.post(f"/api/v1/quests/{quest_id}/start")
    assert second.status_code == 409
    assert second.json()["error_code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_submit_without_start(client: AsyncClient, seeded_user_and_quest):
    _, quest_id = seeded_user_and_quest

    response = await client.post(
        f"/api/v1/quests/{quest_id}/submit",
        json={
            "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            "cloudinary_public_id": "sample",
            "file_hash": "a" * 32,
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_submit_after_start_success(client: AsyncClient, seeded_user_and_quest):
    _, quest_id = seeded_user_and_quest

    start_response = await client.post(f"/api/v1/quests/{quest_id}/start")
    assert start_response.status_code == 201

    submit_response = await client.post(
        f"/api/v1/quests/{quest_id}/submit",
        json={
            "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            "cloudinary_public_id": "sample",
            "file_hash": "b" * 32,
        },
    )
    assert submit_response.status_code == 201
    data = submit_response.json()
    assert data["status"] == "submitted"
    assert data["submission_status"] == "pending"


@pytest.mark.asyncio
async def test_admin_approve_submission_grants_xp_once(client: AsyncClient, admin_client: AsyncClient, seeded_user_and_quest):
    user_id, quest_id = seeded_user_and_quest

    await client.post(f"/api/v1/quests/{quest_id}/start")
    submit_response = await client.post(
        f"/api/v1/quests/{quest_id}/submit",
        json={
            "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            "cloudinary_public_id": "sample",
            "file_hash": "c" * 32,
        },
    )
    submission_id = submit_response.json()["submission_id"]

    approve_response = await admin_client.patch(f"/api/v1/admin/submissions/{submission_id}/approve")
    assert approve_response.status_code == 200
    assert approve_response.json()["xp_granted"] == 100

    async with TestSessionLocal() as session:
        user = await session.scalar(select(User).where(User.id == user_id))
        assert user is not None
        assert user.xp == 100

        submission = await session.scalar(select(Submission).where(Submission.id == uuid.UUID(submission_id)))
        assert submission is not None
        assert submission.status == SubmissionStatus.APPROVED

        user_quest = await session.scalar(select(UserQuest).where(UserQuest.user_id == user_id, UserQuest.quest_id == quest_id))
        assert user_quest is not None
        assert user_quest.status == UserQuestStatus.APPROVED

        xp_rows = await session.execute(select(XpTransaction).where(XpTransaction.submission_id == uuid.UUID(submission_id)))
        assert len(xp_rows.scalars().all()) == 1


@pytest.mark.asyncio
async def test_xp_service_idempotent_for_same_submission(client: AsyncClient, seeded_user_and_quest):
    user_id, quest_id = seeded_user_and_quest

    await client.post(f"/api/v1/quests/{quest_id}/start")
    submit_response = await client.post(
        f"/api/v1/quests/{quest_id}/submit",
        json={
            "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            "cloudinary_public_id": "sample",
            "file_hash": "d" * 32,
        },
    )
    submission_id = uuid.UUID(submit_response.json()["submission_id"])

    async with TestSessionLocal() as session:
        repository = SubmissionRepository(session)
        service = XpService(repository)

        first = await service.grant_for_submission(user_id=user_id, submission_id=submission_id, amount=30)
        second = await service.grant_for_submission(user_id=user_id, submission_id=submission_id, amount=30)
        await session.commit()

        assert first == 30
        assert second == 0


@pytest.mark.asyncio
async def test_admin_reject_submission_sets_status(client: AsyncClient, admin_client: AsyncClient, seeded_user_and_quest):
    user_id, quest_id = seeded_user_and_quest

    await client.post(f"/api/v1/quests/{quest_id}/start")
    submit_response = await client.post(
        f"/api/v1/quests/{quest_id}/submit",
        json={
            "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            "cloudinary_public_id": "sample",
            "file_hash": "e" * 32,
        },
    )
    submission_id = submit_response.json()["submission_id"]

    reject_response = await admin_client.patch(
        f"/api/v1/admin/submissions/{submission_id}/reject",
        json={"reason": "Evidence is invalid"},
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"

    async with TestSessionLocal() as session:
        submission = await session.scalar(select(Submission).where(Submission.id == uuid.UUID(submission_id)))
        assert submission is not None
        assert submission.status == SubmissionStatus.REJECTED

        user_quest = await session.scalar(select(UserQuest).where(UserQuest.user_id == user_id, UserQuest.quest_id == quest_id))
        assert user_quest is not None
        assert user_quest.status == UserQuestStatus.REJECTED


@pytest.mark.asyncio
async def test_admin_endpoints_require_admin_role(client: AsyncClient):
    response = await client.get("/api/v1/admin/submissions")
    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_admin_list_submissions_invalid_status_returns_422(admin_client: AsyncClient):
    response = await admin_client.get("/api/v1/admin/submissions", params={"status": "invalid_status"})
    assert response.status_code == 422
    assert response.json()["error_code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_admin_list_submissions_filter_pending(admin_client: AsyncClient):
    response = await admin_client.get("/api/v1/admin/submissions", params={"status": "pending"})
    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert "total" in payload


@pytest.mark.asyncio
async def test_admin_approve_twice_returns_conflict_and_no_extra_xp(
    client: AsyncClient,
    admin_client: AsyncClient,
    seeded_user_and_quest,
):
    user_id, quest_id = seeded_user_and_quest

    await client.post(f"/api/v1/quests/{quest_id}/start")
    submit_response = await client.post(
        f"/api/v1/quests/{quest_id}/submit",
        json={
            "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            "cloudinary_public_id": "sample",
            "file_hash": "f" * 32,
        },
    )
    submission_id = submit_response.json()["submission_id"]

    first_approve = await admin_client.patch(f"/api/v1/admin/submissions/{submission_id}/approve")
    assert first_approve.status_code == 200

    second_approve = await admin_client.patch(f"/api/v1/admin/submissions/{submission_id}/approve")
    assert second_approve.status_code == 409
    assert second_approve.json()["error_code"] == "CONFLICT"

    async with TestSessionLocal() as session:
        user = await session.scalar(select(User).where(User.id == user_id))
        assert user is not None
        assert user.xp == 100

        xp_rows = await session.execute(select(XpTransaction).where(XpTransaction.submission_id == uuid.UUID(submission_id)))
        assert len(xp_rows.scalars().all()) == 1


@pytest.mark.asyncio
async def test_admin_reject_then_approve_is_blocked(
    client: AsyncClient,
    admin_client: AsyncClient,
    seeded_user_and_quest,
):
    _, quest_id = seeded_user_and_quest

    await client.post(f"/api/v1/quests/{quest_id}/start")
    submit_response = await client.post(
        f"/api/v1/quests/{quest_id}/submit",
        json={
            "image_url": "https://res.cloudinary.com/demo/image/upload/sample.jpg",
            "cloudinary_public_id": "sample",
            "file_hash": "g" * 32,
        },
    )
    submission_id = submit_response.json()["submission_id"]

    reject_response = await admin_client.patch(
        f"/api/v1/admin/submissions/{submission_id}/reject",
        json={"reason": "Invalid proof"},
    )
    assert reject_response.status_code == 200

    approve_after_reject = await admin_client.patch(f"/api/v1/admin/submissions/{submission_id}/approve")
    assert approve_after_reject.status_code == 409
    assert approve_after_reject.json()["error_code"] == "CONFLICT"
