import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.enums import ActivityLevel, QuestDifficulty, UserQuestStatus
from app.models.quest import Category, Quest
from app.models.recommendation import RecommendationLog, TrendingScore, UserQuestStats
from app.models.social import Follow
from app.models.user_preference import UserPreference
from app.models.user_quest import UserQuest
from app.models.poi import Poi

from app.schemas.recommendation import (
    RecommendationListResponse,
    RecommendationQuestItem,
    RecommendationLogRequest,
    RecommendationReasonCode,
    RecommendationScoreBreakdown,
)
from app.services.recommendation.ml.feature_builder import build_feature_snapshot, encode_activity_level
from app.services.recommendation.ml.ml_ranker import get_ml_ranker
from app.services.quest.quest_renderer import render_quest_text


class RecommendationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_recommended_quests(
        self,
        *,
        user_id: uuid.UUID,
        onboarding_completed: bool,
        page: int,
        page_size: int,
        lat: float | None = None,
        lng: float | None = None,
    ) -> RecommendationListResponse:
        request_id = uuid.uuid4()

        preference = await self.db.scalar(select(UserPreference).where(UserPreference.user_id == user_id))
        preferred_categories = set(preference.interests if preference else [])
        activity_level = preference.activity_level if preference else None

        candidate_ids, candidate_sources = await self._generate_candidate_ids(
            user_id=user_id,
            preferred_categories=preferred_categories,
            lat=lat,
            lng=lng,
        )

        candidate_ids = await self._apply_cooldown(user_id=user_id, quest_ids=candidate_ids)
        if not candidate_ids:
            candidate_ids, candidate_sources = await self._fallback_candidate_ids()

        quests = await self._fetch_candidates(candidate_ids)

        user_quest_rows = await self.db.execute(
            select(UserQuest.quest_id, UserQuest.status).where(UserQuest.user_id == user_id)
        )
        status_map: dict[uuid.UUID, UserQuestStatus] = {
            quest_id: status for quest_id, status in user_quest_rows.all()
        }
        social_counts = await self._get_friend_completion_counts(user_id=user_id)

        quest_category_map = {
            quest.id: [category.id for category in quest.categories] for quest in quests
        }
        user_stats = await self._get_user_stats(user_id=user_id)
        ml_ranker = get_ml_ranker(
            model_path=settings.ML_MODEL_PATH or None,
            feature_schema_path=settings.ML_FEATURE_SCHEMA_PATH or None,
        )
        feature_snapshots: dict[uuid.UUID, dict[str, float]] = {}
        score_snapshots: dict[uuid.UUID, dict[str, float | None]] = {}

        items: list[RecommendationQuestItem] = []
        for quest in quests:
            status = status_map.get(quest.id, UserQuestStatus.NOT_STARTED)
            if status in {UserQuestStatus.SUBMITTED, UserQuestStatus.APPROVED}:
                continue

            friend_completed_count = social_counts.get(quest.id, 0)
            source_tags = candidate_sources.get(quest.id, set())
            score, reasons, breakdown = self._score_quest(
                quest=quest,
                preferred_categories=preferred_categories,
                activity_level=activity_level,
                onboarding_completed=onboarding_completed,
                status=status,
                friend_completed_count=friend_completed_count,
                source_tags=source_tags,
            )
            feature_snapshot = self._build_feature_snapshot(
                user_stats=user_stats,
                activity_level=activity_level,
                quest=quest,
                friend_completed_count=friend_completed_count,
                source_tags=source_tags,
            )
            ml_score = ml_ranker.score(feature_snapshot)
            final_score = score + (ml_score or 0.0)
            breakdown.ml_score = float(ml_score or 0.0)
            breakdown.final_score = float(final_score)

            feature_snapshots[quest.id] = feature_snapshot
            score_snapshots[quest.id] = {
                "rule_score": float(score),
                "ml_score": float(ml_score) if ml_score is not None else None,
                "final_score": float(final_score),
            }
            items.append(
                RecommendationQuestItem(
                    id=quest.id,
                    rendered_text=render_quest_text(quest.template, quest.labels, None),
                    title=quest.title,
                    description=quest.description,
                    difficulty=quest.difficulty.value if hasattr(quest.difficulty, 'value') else str(quest.difficulty),
                    image_url=None, # Fallback as DB lacks this currently
                    labels=quest.labels or [],
                    min_confidence=float(quest.min_confidence or 0.5),
                    poi_required=quest.poi_required,
                    xp_reward=quest.xp_reward,
                    user_status=status,
                    recommendation_score=round(final_score, 3),
                    ml_score=round(float(ml_score), 3) if ml_score is not None else None,
                    reasons=reasons,
                    score_breakdown=breakdown,
                )
            )


        items.sort(key=lambda row: row.recommendation_score, reverse=True)
        items = self._apply_diversity(
            items=items,
            quest_category_map=quest_category_map,
            max_per_category=3,
        )
        total = len(items)

        offset = (page - 1) * page_size
        paged_items = items[offset : offset + page_size]
        response = RecommendationListResponse.create(
            items=paged_items,
            total=total,
            page=page,
            page_size=page_size,
            request_id=request_id,
        )

        await self._log_shown_events(
            user_id=user_id,
            request_id=request_id,
            items=paged_items,
            feature_snapshots=feature_snapshots,
            score_snapshots=score_snapshots,
        )
        return response

    async def log_event(self, *, user_id: uuid.UUID, payload: RecommendationLogRequest) -> None:
        record = RecommendationLog(
            user_id=user_id,
            quest_id=payload.quest_id,
            event=payload.event.value,
            score=payload.score,
            rank=payload.rank,
            request_id=payload.request_id,
            reasons=[reason.value for reason in payload.reasons],
            score_breakdown=payload.score_breakdown.model_dump() if payload.score_breakdown else None,
            features_snapshot=payload.features_snapshot,
            rule_score=payload.rule_score,
            ml_score=payload.ml_score,
            final_score=payload.final_score,
        )
        self.db.add(record)
        await self.db.commit()

    async def _log_shown_events(
        self,
        *,
        user_id: uuid.UUID,
        request_id: uuid.UUID,
        items: list[RecommendationQuestItem],
        feature_snapshots: dict[uuid.UUID, dict[str, float]],
        score_snapshots: dict[uuid.UUID, dict[str, float | None]],
    ) -> None:
        for index, item in enumerate(items, start=1):
            score_snapshot = score_snapshots.get(item.id, {})
            self.db.add(
                RecommendationLog(
                    user_id=user_id,
                    quest_id=item.id,
                    event="shown",
                    score=float(item.recommendation_score),
                    rank=index,
                    request_id=request_id,
                    reasons=[reason.value for reason in item.reasons],
                    score_breakdown=item.score_breakdown.model_dump() if item.score_breakdown else None,
                    features_snapshot=feature_snapshots.get(item.id),
                    rule_score=score_snapshot.get("rule_score"),
                    ml_score=score_snapshot.get("ml_score"),
                    final_score=score_snapshot.get("final_score"),
                )
            )
        await self.db.commit()

    async def _generate_candidate_ids(
        self,
        *,
        user_id: uuid.UUID,
        preferred_categories: set[int],
        lat: float | None = None,
        lng: float | None = None,
    ) -> tuple[list[uuid.UUID], dict[uuid.UUID, set[str]]]:
        candidate_ids: list[uuid.UUID] = []
        candidate_sources: dict[uuid.UUID, set[str]] = {}
        seen: set[uuid.UUID] = set()

        def add_ids(ids: list[uuid.UUID], source: str) -> None:
            for quest_id in ids:
                candidate_sources.setdefault(quest_id, set()).add(source)
                if quest_id in seen:
                    continue
                seen.add(quest_id)
                candidate_ids.append(quest_id)

        # HIGH PRIORITY: Location based recommendation
        if lat is not None and lng is not None:
            nearby_ids = await self._fetch_nearby_ids(lat=lat, lng=lng, limit=50)
            add_ids(nearby_ids, "nearby")


        trending_ids = await self._fetch_trending_ids(limit=60)
        add_ids(trending_ids, "trending")

        social_ids = await self._fetch_social_ids(user_id=user_id, limit=60)
        add_ids(social_ids, "social")

        category_ids = await self._fetch_category_ids(preferred_categories=preferred_categories, limit=80)
        add_ids(category_ids, "category")

        recent_ids = await self._fetch_recent_ids(limit=60)
        add_ids(recent_ids, "recent")

        exploration_ids = await self._fetch_exploration_ids(exclude_ids=seen, limit=30)
        add_ids(exploration_ids, "exploration")

        return candidate_ids[:200], candidate_sources

    async def _fallback_candidate_ids(self) -> tuple[list[uuid.UUID], dict[uuid.UUID, set[str]]]:
        recent_ids = await self._fetch_recent_ids(limit=80)
        candidate_sources = {quest_id: {"recent"} for quest_id in recent_ids}
        return recent_ids, candidate_sources

    async def _fetch_nearby_ids(self, *, lat: float, lng: float, limit: int) -> list[uuid.UUID]:
        # Define approx search boundary: 0.045 deg is ~5km in most regions
        LAT_WINDOW = 0.05
        LNG_WINDOW = 0.05
        
        rows = await self.db.execute(
            select(Quest.id)
            .join(Poi, Quest.poi_id == Poi.id)
            .where(
                Quest.is_active.is_(True),
                Poi.latitude.between(lat - LAT_WINDOW, lat + LAT_WINDOW),
                Poi.longitude.between(lng - LNG_WINDOW, lng + LNG_WINDOW)
            )
            .limit(limit)
        )
        return [row[0] for row in rows.all()]


    async def _fetch_recent_ids(self, *, limit: int) -> list[uuid.UUID]:
        rows = await self.db.execute(
            select(Quest.id)
            .where(Quest.is_active.is_(True))
            .order_by(Quest.created_at.desc())
            .limit(limit)
        )
        return [row[0] for row in rows.all()]

    async def _fetch_category_ids(self, *, preferred_categories: set[int], limit: int) -> list[uuid.UUID]:
        if not preferred_categories:
            return []
        rows = await self.db.execute(
            select(Quest.id)
            .join(Quest.categories)
            .where(Category.id.in_(preferred_categories), Quest.is_active.is_(True))
            .order_by(Quest.created_at.desc())
            .limit(limit)
        )
        return [row[0] for row in rows.all()]

    async def _fetch_social_ids(self, *, user_id: uuid.UUID, limit: int) -> list[uuid.UUID]:
        rows = await self.db.execute(
            select(UserQuest.quest_id)
            .join(Follow, Follow.following_id == UserQuest.user_id)
            .where(Follow.follower_id == user_id, UserQuest.status == UserQuestStatus.APPROVED)
            .group_by(UserQuest.quest_id)
            .order_by(func.count().desc())
            .limit(limit)
        )
        return [row[0] for row in rows.all()]

    async def _fetch_trending_ids(self, *, limit: int) -> list[uuid.UUID]:
        rows = await self.db.execute(
            select(TrendingScore.quest_id)
            .where(TrendingScore.window == "7d")
            .order_by(TrendingScore.score.desc())
            .limit(limit)
        )
        return [row[0] for row in rows.all()]

    async def _fetch_exploration_ids(
        self,
        *,
        exclude_ids: set[uuid.UUID],
        limit: int,
    ) -> list[uuid.UUID]:
        stmt = select(Quest.id).where(Quest.is_active.is_(True))
        if exclude_ids:
            stmt = stmt.where(Quest.id.notin_(exclude_ids))
        rows = await self.db.execute(stmt.order_by(func.random()).limit(limit))
        return [row[0] for row in rows.all()]

    async def _apply_cooldown(
        self,
        *,
        user_id: uuid.UUID,
        quest_ids: list[uuid.UUID],
    ) -> list[uuid.UUID]:
        if not quest_ids:
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        rows = await self.db.execute(
            select(RecommendationLog.quest_id)
            .where(
                RecommendationLog.user_id == user_id,
                RecommendationLog.event == "shown",
                RecommendationLog.created_at >= cutoff,
            )
        )
        recently_shown = {row[0] for row in rows.all()}
        filtered = [quest_id for quest_id in quest_ids if quest_id not in recently_shown]
        return filtered or quest_ids

    async def _fetch_candidates(self, quest_ids: list[uuid.UUID]) -> list[Quest]:
        if not quest_ids:
            return []
        rows = await self.db.scalars(
            select(Quest)
            .options(selectinload(Quest.categories))
            .where(Quest.id.in_(quest_ids))
        )
        quest_map = {quest.id: quest for quest in rows.all()}
        return [quest_map[quest_id] for quest_id in quest_ids if quest_id in quest_map]

    async def _get_friend_completion_counts(self, *, user_id: uuid.UUID) -> dict[uuid.UUID, int]:
        rows = await self.db.execute(
            select(UserQuest.quest_id, func.count().label("friend_count"))
            .join(Follow, Follow.following_id == UserQuest.user_id)
            .where(Follow.follower_id == user_id, UserQuest.status == UserQuestStatus.APPROVED)
            .group_by(UserQuest.quest_id)
        )
        return {quest_id: int(count) for quest_id, count in rows.all()}

    @staticmethod
    def _score_quest(
        *,
        quest: Quest,
        preferred_categories: set[int],
        activity_level: ActivityLevel | None,
        onboarding_completed: bool,
        status: UserQuestStatus,
        friend_completed_count: int,
        source_tags: set[str],
    ) -> tuple[float, list[RecommendationReasonCode], RecommendationScoreBreakdown]:
        reasons: list[RecommendationReasonCode] = []
        breakdown = RecommendationScoreBreakdown()
        score = 1.0
        breakdown.base_score = 1.0

        if status == UserQuestStatus.STARTED:
            score += 2.0
            breakdown.status_score = 2.0
            reasons.append(RecommendationReasonCode.IN_PROGRESS)

        if preferred_categories:
            quest_category_ids = {category.id for category in quest.categories}
            overlap = len(preferred_categories.intersection(quest_category_ids))
            if overlap > 0:
                category_score = overlap * 1.5
                score += category_score
                breakdown.category_score = category_score
                reasons.append(RecommendationReasonCode.MATCH_CATEGORY)

        difficulty_boost = {
            ActivityLevel.LOW: {QuestDifficulty.EASY: 1.0, QuestDifficulty.MEDIUM: 0.3, QuestDifficulty.HARD: 0.0},
            ActivityLevel.MEDIUM: {QuestDifficulty.EASY: 0.5, QuestDifficulty.MEDIUM: 1.0, QuestDifficulty.HARD: 0.5},
            ActivityLevel.HIGH: {QuestDifficulty.EASY: 0.2, QuestDifficulty.MEDIUM: 0.8, QuestDifficulty.HARD: 1.2},
        }

        if activity_level:
            difficulty_score = difficulty_boost.get(activity_level, {}).get(quest.difficulty, 0.0)
            score += difficulty_score
            breakdown.difficulty_score = difficulty_score
            if difficulty_score > 0:
                reasons.append(RecommendationReasonCode.FIT_ACTIVITY_LEVEL)
        elif not onboarding_completed and quest.difficulty == QuestDifficulty.EASY:
            score += 0.5
            breakdown.difficulty_score = 0.5
            reasons.append(RecommendationReasonCode.ONBOARDING_EASY)

        xp_score = min(quest.xp_reward / 500.0, 1.0)
        score += xp_score
        breakdown.xp_score = xp_score
        if xp_score >= 0.6:
            reasons.append(RecommendationReasonCode.HIGH_XP)

        if friend_completed_count > 0:
            social_score = min(friend_completed_count * 0.3, 1.2)
            score += social_score
            breakdown.social_score = social_score
            reasons.append(RecommendationReasonCode.FRIENDS_COMPLETED)

        freshness_score = RecommendationService._freshness_score(quest.created_at)
        if freshness_score > 0:
            score += freshness_score
            breakdown.freshness_score = freshness_score
            reasons.append(RecommendationReasonCode.FRESH)

        if quest.location_required:
            score -= 0.2
            breakdown.location_penalty = -0.2
            reasons.append(RecommendationReasonCode.LOCATION_REQUIRED)

        if "trending" in source_tags:
            reasons.append(RecommendationReasonCode.TRENDING)
        if "exploration" in source_tags:
            reasons.append(RecommendationReasonCode.EXPLORATION)
        if "nearby" in source_tags:
            score += 5.0  # Major boost for proximity
            reasons.append(RecommendationReasonCode.NEARBY)

        breakdown.rule_score = score
        return score, reasons, breakdown


    async def _get_user_stats(self, *, user_id: uuid.UUID) -> dict[str, float]:
        rows = await self.db.execute(
            select(UserQuest.status, func.count().label("count"))
            .where(UserQuest.user_id == user_id)
            .group_by(UserQuest.status)
        )
        counts = {status: int(count) for status, count in rows.all()}
        completed = counts.get(UserQuestStatus.APPROVED, 0)
        started = counts.get(UserQuestStatus.STARTED, 0)
        total = completed + started
        completion_rate = completed / total if total > 0 else 0.0

        retry_count = await self.db.scalar(
            select(func.sum(UserQuestStats.retry_count)).where(UserQuestStats.user_id == user_id)
        )

        return {
            "completion_rate": float(completion_rate),
            "retry_count": float(retry_count or 0.0),
            "streak_days": 0.0,
        }

    @staticmethod
    def _build_feature_snapshot(
        *,
        user_stats: dict[str, float],
        activity_level: ActivityLevel | None,
        quest: Quest,
        friend_completed_count: int,
        source_tags: set[str],
    ) -> dict[str, float]:
        popularity = 0.3
        if "trending" in source_tags:
            popularity = 0.9
        elif "social" in source_tags:
            popularity = 0.7
        elif "recent" in source_tags:
            popularity = 0.5

        freshness_raw = RecommendationService._freshness_score(quest.created_at)
        freshness_score = min(freshness_raw / 0.6, 1.0) if freshness_raw > 0 else 0.0
        ai_required_score = 1.0 if quest.poi_required or quest.vision_spec else 0.0

        return build_feature_snapshot(
            {
                "completion_rate": user_stats.get("completion_rate", 0.0),
                "activity_level": encode_activity_level(activity_level) if activity_level else 0.5,
                "streak_days": user_stats.get("streak_days", 0.0),
                "avg_difficulty_pref": encode_activity_level(activity_level) if activity_level else 0.5,
            },
            {
                "difficulty": quest.difficulty,
                "popularity": popularity,
                "freshness_score": freshness_score,
                "ai_required_score": ai_required_score,
            },
            {
                "retry_count": user_stats.get("retry_count", 0.0),
                "friend_completed_count": float(friend_completed_count),
            },
        )

    @staticmethod
    def _freshness_score(created_at: datetime | None) -> float:
        if not created_at:
            return 0.0
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        age_days = max((now - created_at).days, 0)
        if age_days <= 7:
            return 0.6
        if age_days <= 30:
            return 0.2
        return 0.0

    @staticmethod
    def _apply_diversity(
        *,
        items: list[RecommendationQuestItem],
        quest_category_map: dict[uuid.UUID, list[int]],
        max_per_category: int,
    ) -> list[RecommendationQuestItem]:
        if not items:
            return items

        category_counts: dict[int, int] = {}
        diversified: list[RecommendationQuestItem] = []
        remaining: list[RecommendationQuestItem] = []

        for item in items:
            category_ids = quest_category_map.get(item.id, [])
            if not category_ids:
                diversified.append(item)
                continue

            if any(category_counts.get(category_id, 0) < max_per_category for category_id in category_ids):
                diversified.append(item)
                for category_id in category_ids:
                    category_counts[category_id] = category_counts.get(category_id, 0) + 1
            else:
                remaining.append(item)

        return diversified + remaining
