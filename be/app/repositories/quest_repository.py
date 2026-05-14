import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import SubmissionStatus
from app.models.quest import Quest
from app.models.submission import Submission
from app.models.user_quest import UserQuest
from app.models.poi import Poi


class QuestRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_nearby_active_quests(self, *, lat: float, lng: float, limit: int = 100) -> list[Quest]:
        # Define bounding window box of ~5km
        WINDOW = 0.05
        stmt = (
            select(Quest)
            .join(Poi, Quest.poi_id == Poi.id)
            .where(
                Quest.is_active.is_(True),
                Poi.latitude.between(lat - WINDOW, lat + WINDOW),
                Poi.longitude.between(lng - WINDOW, lng + WINDOW)
            )
            .order_by(Quest.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


    async def list_active_quests(self, *, offset: int, limit: int) -> tuple[list[Quest], int]:
        total_stmt = select(func.count()).select_from(Quest).where(Quest.is_active.is_(True))
        total = await self.db.scalar(total_stmt)

        stmt = (
            select(Quest)
            .where(Quest.is_active.is_(True))
            .order_by(Quest.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), int(total or 0)

    async def get_quest_by_id(self, quest_id: uuid.UUID) -> Quest | None:
        return await self.db.scalar(select(Quest).where(Quest.id == quest_id))

    async def get_user_quest(self, *, user_id: uuid.UUID, quest_id: uuid.UUID) -> UserQuest | None:
        stmt = select(UserQuest).where(
            UserQuest.user_id == user_id,
            UserQuest.quest_id == quest_id,
        )
        return await self.db.scalar(stmt)

    async def get_user_quest_for_update(self, *, user_id: uuid.UUID, quest_id: uuid.UUID) -> UserQuest | None:
        stmt = (
            select(UserQuest)
            .where(
                UserQuest.user_id == user_id,
                UserQuest.quest_id == quest_id,
            )
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user_quest(
        self,
        *,
        user_id: uuid.UUID,
        quest_id: uuid.UUID,
        status: str,
        started_at: datetime,
        expires_at: datetime | None,
    ) -> UserQuest:
        item = UserQuest(
            user_id=user_id,
            quest_id=quest_id,
            status=status,
            started_at=started_at,
            expires_at=expires_at,
        )
        self.db.add(item)
        await self.db.flush()
        return item

    async def get_submission_by_user_quest_id(self, user_quest_id: uuid.UUID) -> Submission | None:
        stmt = select(Submission).where(Submission.user_quest_id == user_quest_id)
        return await self.db.scalar(stmt)

    async def create_submission(
        self,
        *,
        user_quest_id: uuid.UUID,
        image_url: str,
        cloudinary_public_id: str,
        file_hash: str,
        lat: float | None = None,
        lng: float | None = None,
        location_accuracy_m: float | None = None,
        location_captured_at: datetime | None = None,
    ) -> Submission:
        submission = Submission(
            user_quest_id=user_quest_id,
            image_url=image_url,
            cloudinary_public_id=cloudinary_public_id,
            file_hash=file_hash,
            lat=lat,
            lng=lng,
            location_accuracy_m=location_accuracy_m,
            location_captured_at=location_captured_at,
            status=SubmissionStatus.PENDING,
            is_suspicious=False,
        )
        self.db.add(submission)
        await self.db.flush()
        return submission

    async def update_rejected_submission_for_retry(
        self,
        submission: Submission,
        *,
        image_url: str,
        cloudinary_public_id: str,
        file_hash: str,
        lat: float | None = None,
        lng: float | None = None,
        location_accuracy_m: float | None = None,
        location_captured_at: datetime | None = None,
    ) -> Submission:
        submission.image_url = image_url
        submission.cloudinary_public_id = cloudinary_public_id
        submission.file_hash = file_hash
        submission.lat = lat
        submission.lng = lng
        submission.location_accuracy_m = location_accuracy_m
        submission.location_captured_at = location_captured_at
        submission.retry_count += 1
        submission.status = SubmissionStatus.PENDING
        submission.rejection_reason = None
        submission.is_suspicious = False
        submission.ai_score = None
        submission.cheat_flags = None
        submission.vision_labels = None
        submission.vision_raw = None
        submission.ai_metadata = None
        submission.poi_id = None
        submission.poi_distance_m = None
        await self.db.flush()
        return submission

    async def commit(self) -> None:
        await self.db.commit()
