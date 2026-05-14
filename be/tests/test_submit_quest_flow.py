import uuid
from datetime import datetime, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.enums import SubmissionStatus
from app.models.quest import Quest
from app.models.submission import Submission
from app.models.user import User
from app.models.user_quest import UserQuest
from app.workers.approval_tasks import _process_submission_ai


TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_submit_flow.db"


test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def seeded_flow_data(monkeypatch):
    async with TestSessionLocal() as session:
        user_id = uuid.uuid4()
        quest_id = uuid.uuid4()
        user_quest_id = uuid.uuid4()
        submission_id = uuid.uuid4()

        user = User(
            id=user_id,
            username=f"flow_user_{user_id.hex[:6]}",
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
            template="Take a photo of a {label}",
            labels=["coffee"],
            min_confidence=0.5,
            poi_required=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        user_quest = UserQuest(
            id=user_quest_id,
            user_id=user_id,
            quest_id=quest_id,
            status="submitted",
            started_at=datetime.now(timezone.utc),
            expires_at=None,
        )
        submission = Submission(
            id=submission_id,
            user_quest_id=user_quest_id,
            image_url="https://res.cloudinary.com/demo/image/upload/sample.jpg",
            cloudinary_public_id="sample",
            file_hash="x" * 32,
            status=SubmissionStatus.PENDING,
            is_suspicious=False,
            created_at=datetime.now(timezone.utc),
            lat=16.06,
            lng=108.22,
        )

        session.add_all([user, quest, user_quest, submission])
        await session.commit()

        return submission_id


@pytest.mark.asyncio
async def test_submit_quest_flow(monkeypatch, seeded_flow_data):
    from app.services.vision.vision_service import VisionResult, VisionLabel
    from app.services.poi.poi_matcher import PoiMatch
    from app.models.poi import Poi
    from app.workers import approval_tasks

    async with TestSessionLocal() as session:
        poi = Poi(
            name="Cafe Test",
            poi_type="cafe",
            latitude=16.06,
            longitude=108.22,
            radius_m=40.0,
            source="manual",
            external_id=str(uuid.uuid4()),
            is_active=True,
        )
        session.add(poi)
        await session.commit()

    def fake_detect_labels(*_args, **_kwargs):
        return VisionResult(labels=[VisionLabel("coffee", 0.9)], raw_response={"mock": True})

    async def fake_match_poi(*_args, **_kwargs):
        return PoiMatch(poi=poi, distance_m=10.0)

    monkeypatch.setattr(
        "app.services.vision.vision_service.VisionService.detect_labels_from_url",
        fake_detect_labels,
    )
    monkeypatch.setattr(
        "app.services.vision.vision_service.VisionService.__init__",
        lambda self: None,
    )
    monkeypatch.setattr("app.services.poi.poi_matcher.match_poi", fake_match_poi)
    monkeypatch.setattr(approval_tasks, "AsyncSessionLocal", TestSessionLocal)

    await _process_submission_ai(str(seeded_flow_data))

    async with TestSessionLocal() as session:
        submission = await session.get(Submission, seeded_flow_data)
        assert submission is not None
        assert submission.status == SubmissionStatus.APPROVED
        assert submission.ai_metadata is not None
        assert submission.ai_metadata["matched_label"] == "coffee"
        assert submission.ai_metadata["poi_validated"] is True


@pytest.mark.asyncio
async def test_submit_quest_flow_reject_low_confidence(monkeypatch, seeded_flow_data):
    from app.services.vision.vision_service import VisionResult, VisionLabel
    from app.workers import approval_tasks

    def fake_detect_labels(*_args, **_kwargs):
        return VisionResult(labels=[VisionLabel("coffee", 0.2)], raw_response={"mock": True})

    async def fake_match_poi(*_args, **_kwargs):
        return None

    monkeypatch.setattr(
        "app.services.vision.vision_service.VisionService.detect_labels_from_url",
        fake_detect_labels,
    )
    monkeypatch.setattr(
        "app.services.vision.vision_service.VisionService.__init__",
        lambda self: None,
    )
    monkeypatch.setattr("app.services.poi.poi_matcher.match_poi", fake_match_poi)
    monkeypatch.setattr(approval_tasks, "AsyncSessionLocal", TestSessionLocal)

    await _process_submission_ai(str(seeded_flow_data))

    async with TestSessionLocal() as session:
        submission = await session.get(Submission, seeded_flow_data)
        assert submission is not None
        assert submission.status == SubmissionStatus.REJECTED
        assert submission.ai_metadata is not None
        assert submission.ai_metadata["reason"] in {"label_not_matched", "poi_required_missing"}


@pytest.mark.asyncio
async def test_submit_quest_flow_reject_missing_poi(monkeypatch, seeded_flow_data):
    from app.services.vision.vision_service import VisionResult, VisionLabel
    from app.workers import approval_tasks

    def fake_detect_labels(*_args, **_kwargs):
        return VisionResult(labels=[VisionLabel("coffee", 0.9)], raw_response={"mock": True})

    async def fake_match_poi(*_args, **_kwargs):
        return None

    monkeypatch.setattr(
        "app.services.vision.vision_service.VisionService.detect_labels_from_url",
        fake_detect_labels,
    )
    monkeypatch.setattr(
        "app.services.vision.vision_service.VisionService.__init__",
        lambda self: None,
    )
    monkeypatch.setattr("app.services.poi.poi_matcher.match_poi", fake_match_poi)
    monkeypatch.setattr(approval_tasks, "AsyncSessionLocal", TestSessionLocal)

    await _process_submission_ai(str(seeded_flow_data))

    async with TestSessionLocal() as session:
        submission = await session.get(Submission, seeded_flow_data)
        assert submission is not None
        assert submission.status == SubmissionStatus.REJECTED
        assert submission.ai_metadata is not None
        assert submission.ai_metadata["reason"] == "poi_required_missing"
