import uuid
from datetime import datetime

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import redis_get, redis_set
from app.models.enums import SubmissionStatus, UserQuestStatus
from app.models.poi import Poi
from app.models.quest import Quest
from app.models.social import Post
from app.models.quest_instance import QuestInstance
from app.models.submission import Submission
from app.models.user_quest import UserQuest


class QuestRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    _title_image_cache_ttl_s = 300
    _title_image_cache_prefix = "quest:title_image"
    _title_image_cache_empty = "__none__"

    async def list_nearby_active_quests(self, *, lat: float, lng: float, limit: int = 100) -> list[Quest]:
        stmt = (
            select(Quest)
            .where(Quest.is_active.is_(True))
            .order_by(Quest.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_active_quests(self, *, offset: int, limit: int) -> tuple[list[Quest], int]:
        total_stmt = (
            select(func.count())
            .select_from(Quest)
            .where(Quest.is_active.is_(True))
            .where(Quest.is_event.is_(False))
        )
        total = await self.db.scalar(total_stmt)

        stmt = (
            select(Quest)
            .where(Quest.is_active.is_(True))
            .where(Quest.is_event.is_(False))
            .order_by(Quest.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), int(total or 0)

    async def list_user_quest_instances(
        self,
        *,
        user_id: uuid.UUID,
    ) -> list[tuple[UserQuest, Quest, Poi | None]]:
        stmt = (
            select(UserQuest, Quest, Poi)
            .join(Quest, Quest.id == UserQuest.quest_id)
            .outerjoin(Poi, Poi.id == UserQuest.poi_id)
            .where(
                UserQuest.user_id == user_id,
                or_(
                    UserQuest.poi_id.is_not(None),
                    Quest.is_event.is_(True)
                ),
                Quest.is_active.is_(True),
            )
            .order_by(UserQuest.started_at.desc())
        )
        result = await self.db.execute(stmt)
        return [(user_quest, quest, poi) for user_quest, quest, poi in result.all()]

    async def get_quest_by_id(self, quest_id: uuid.UUID) -> Quest | None:
        stmt = select(Quest).where(Quest.id == quest_id)
        return await self.db.scalar(stmt)

    async def get_poi_by_id(self, poi_id: uuid.UUID) -> Poi | None:
        stmt = select(Poi).where(Poi.id == poi_id, Poi.is_active.is_(True))
        return await self.db.scalar(stmt)

    async def get_user_quest(
        self,
        *,
        user_id: uuid.UUID,
        quest_id: uuid.UUID,
        poi_id: uuid.UUID | None = None,
    ) -> UserQuest | None:
        stmt = select(UserQuest).where(
            UserQuest.user_id == user_id,
            UserQuest.quest_id == quest_id,
        )
        if poi_id is None:
            stmt = stmt.where(UserQuest.poi_id.is_(None))
        else:
            stmt = stmt.where(UserQuest.poi_id == poi_id)
        return await self.db.scalar(stmt)

    async def get_best_user_quest_for_detail(
        self,
        *,
        user_id: uuid.UUID,
        quest_id: uuid.UUID,
    ) -> UserQuest | None:
        status_rank = case(
            (UserQuest.status == UserQuestStatus.APPROVED, 0),
            (UserQuest.status == UserQuestStatus.SUBMITTED, 1),
            (UserQuest.status == UserQuestStatus.STARTED, 2),
            (UserQuest.status == UserQuestStatus.REJECTED, 3),
            else_=4,
        )
        stmt = (
            select(UserQuest)
            .where(
                UserQuest.user_id == user_id,
                UserQuest.quest_id == quest_id,
            )
            .order_by(status_rank, UserQuest.started_at.desc())
            .limit(1)
        )
        return await self.db.scalar(stmt)

    async def get_user_quest_for_update(
        self,
        *,
        user_id: uuid.UUID,
        quest_id: uuid.UUID,
        poi_id: uuid.UUID | None = None,
    ) -> UserQuest | None:
        stmt = (
            select(UserQuest)
            .where(
                UserQuest.user_id == user_id,
                UserQuest.quest_id == quest_id,
            )
            .with_for_update()
        )
        if poi_id is None:
            stmt = stmt.where(UserQuest.poi_id.is_(None))
        else:
            stmt = stmt.where(UserQuest.poi_id == poi_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user_quest(
        self,
        *,
        user_id: uuid.UUID,
        quest_id: uuid.UUID,
        poi_id: uuid.UUID | None,
        status: str,
        started_at: datetime,
    ) -> UserQuest:
        item = UserQuest(
            user_id=user_id,
            quest_id=quest_id,
            poi_id=poi_id,
            status=status,
            started_at=started_at,
        )
        self.db.add(item)
        await self.db.flush()
        return item

    async def create_quest_instance_mapping(
        self,
        *,
        user_id: uuid.UUID,
        quest_id: uuid.UUID,
        poi_id: uuid.UUID,
    ) -> None:
        existing = await self.db.scalar(
            select(QuestInstance).where(
                QuestInstance.user_id == user_id,
                QuestInstance.quest_id == quest_id,
                QuestInstance.poi_id == poi_id,
            )
        )
        if existing is not None:
            return
        self.db.add(QuestInstance(user_id=user_id, quest_id=quest_id, poi_id=poi_id))
        await self.db.flush()

    async def get_submission_by_user_quest_id(self, user_quest_id: uuid.UUID) -> Submission | None:
        stmt = select(Submission).where(Submission.user_quest_id == user_quest_id)
        return await self.db.scalar(stmt)

    async def get_post_for_update(self, *, user_id: uuid.UUID, post_id: uuid.UUID) -> Post | None:
        stmt = select(Post).where(Post.id == post_id, Post.user_id == user_id).with_for_update()
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_post_by_submission_for_update(
        self,
        *,
        user_id: uuid.UUID,
        submission_id: uuid.UUID,
    ) -> Post | None:
        stmt = (
            select(Post)
            .where(Post.user_id == user_id, Post.submission_id == submission_id)
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_post(self, post: Post) -> None:
        await self.db.delete(post)
        await self.db.flush()

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
    ) -> Submission:
        submission = Submission(
            user_quest_id=user_quest_id,
            image_url=image_url,
            cloudinary_public_id=cloudinary_public_id,
            file_hash=file_hash,
            lat=lat,
            lng=lng,
            location_accuracy_m=location_accuracy_m,
            status=SubmissionStatus.PENDING,
            is_suspicious=False,
        )
        self.db.add(submission)
        await self.db.flush()
        return submission

    async def get_top_post_images_for_quests(
        self,
        *,
        quest_ids: list[uuid.UUID],
        since: datetime,
    ) -> dict[uuid.UUID, str]:
        if not quest_ids:
            return {}

        cached: dict[uuid.UUID, str] = {}
        missing: list[uuid.UUID] = []

        try:
            for quest_id in quest_ids:
                cache_key = f"{self._title_image_cache_prefix}:{quest_id}"
                cached_value = await redis_get(cache_key)
                if cached_value is None:
                    missing.append(quest_id)
                elif cached_value != self._title_image_cache_empty:
                    cached[quest_id] = cached_value
        except Exception:
            missing = quest_ids

        if not missing:
            return cached

        quest_id_expr = func.coalesce(Post.quest_id, UserQuest.quest_id)
        image_url_expr = func.coalesce(Post.image_url, Submission.image_url)
        score_expr = (Post.like_count * 3 + Post.comment_count * 5).label("score")

        ranked = (
            select(
                quest_id_expr.label("quest_id"),
                image_url_expr.label("image_url"),
                score_expr,
                Post.created_at.label("created_at"),
                func.row_number()
                .over(
                    partition_by=quest_id_expr,
                    order_by=(score_expr.desc(), Post.created_at.desc()),
                )
                .label("rn"),
            )
            .select_from(Post)
            .outerjoin(Submission, Post.submission_id == Submission.id)
            .outerjoin(UserQuest, Submission.user_quest_id == UserQuest.id)
            .where(
                quest_id_expr.in_(missing),
                Post.created_at >= since,
                image_url_expr.is_not(None),
            )
            .subquery()
        )

        rows = await self.db.execute(
            select(ranked.c.quest_id, ranked.c.image_url).where(ranked.c.rn == 1)
        )
        fresh = {row[0]: row[1] for row in rows.all() if row[0] is not None and row[1] is not None}

        try:
            for quest_id in missing:
                image_url = fresh.get(quest_id)
                cache_key = f"{self._title_image_cache_prefix}:{quest_id}"
                await redis_set(
                    cache_key,
                    image_url or self._title_image_cache_empty,
                    ttl=self._title_image_cache_ttl_s,
                )
        except Exception:
            pass

        cached.update(fresh)
        return cached

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
        increment_retry: bool = True,
    ) -> Submission:
        submission.image_url = image_url
        submission.cloudinary_public_id = cloudinary_public_id
        submission.file_hash = file_hash
        submission.lat = lat
        submission.lng = lng
        submission.location_accuracy_m = location_accuracy_m
        if increment_retry:
            submission.retry_count += 1
        submission.status = SubmissionStatus.PENDING
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
