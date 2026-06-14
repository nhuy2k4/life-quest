import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, case, exists, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import UserQuestStatus
from app.models.poi import Poi
from app.models.quest import Quest, QuestCategory
from app.models.quest_instance import QuestInstance
from app.models.recommendation import RecommendationLog
from app.models.social import Comment, Follow, Like, Post
from app.models.submission import Submission
from app.models.user import User
from app.models.user_preference import UserPreference
from app.models.user_quest import UserQuest
from app.schemas.recommendation import (
	RecommendationDebugInfo,
	RecommendationEventRequest,
	RecommendationListResponse,
	RecommendationPostItem,
	RecommendationQuestItem,
	RecommendationScoreBreakdown,
	RecommendationSection,
	RecommendationSectionKey,
)
from app.schemas.social import PostQuestInfo
from app.schemas.user import UserPublicResponse
from app.services.quest.quest_renderer import render_quest_text
from app.repositories.quest_repository import QuestRepository


ALGORITHM_VERSION = "rule_based_mvp_v1"
EVENT_SCORE_WEIGHTS = {
	"clicked": 2.0,
	"started": 4.0,
	"completed": 6.0,
	"post_liked": 1.0,
	"post_commented": 3.0,
}
SECTION_TITLES = {
	RecommendationSectionKey.RECOMMENDED_FOR_YOU: "Recommended For You",
	RecommendationSectionKey.TRENDING_NEAR_YOU: "Trending Near You",
	RecommendationSectionKey.CONTINUE_YOUR_MISSIONS: "Continue Your Missions",
	RecommendationSectionKey.EXPLORE_NEW_THINGS: "Explore New Things",
}


@dataclass
class CandidateScore:
	quest: Quest
	status: UserQuestStatus
	poi: Poi | None = None
	sources: set[str] = field(default_factory=set)
	breakdown: RecommendationScoreBreakdown = field(default_factory=RecommendationScoreBreakdown)
	reasons: list[str] = field(default_factory=list)
	matched_categories: list[str] = field(default_factory=list)
	nearby_distance_m: float | None = None
	popularity_score: float = 0.0
	affinity_score: float = 0.0
	was_recently_shown: bool = False

	@property
	def final_score(self) -> float:
		return round(
			self.breakdown.interest
			+ self.breakdown.nearby
			+ self.breakdown.trending
			+ self.breakdown.continue_score
			+ self.breakdown.affinity
			+ self.breakdown.anti_repeat
			+ self.breakdown.exploration
			+ self.breakdown.freshness,
			3,
		)


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
		debug: bool = False,
	) -> RecommendationListResponse:
		request_id = uuid.uuid4()
		preference = await self.db.scalar(select(UserPreference).where(UserPreference.user_id == user_id))
		preferred_category_ids = self._normalize_category_ids(preference.interests if preference else [])

		status_map = await self._get_user_status_map(user_id=user_id)
		recently_shown = await self._get_recently_shown(user_id=user_id)
		affinity_by_category = await self._get_category_affinity(user_id=user_id)
		popularity_by_quest = await self._get_popularity_scores()
		candidates = await self._generate_candidates(
			user_id=user_id,
			preferred_category_ids=preferred_category_ids,
			status_map=status_map,
			popularity_by_quest=popularity_by_quest,
			lat=lat,
			lng=lng,
		)
		scored = self._score_candidates(
			candidates=candidates,
			preferred_category_ids=preferred_category_ids,
			status_map=status_map,
			affinity_by_category=affinity_by_category,
			popularity_by_quest=popularity_by_quest,
			recently_shown=recently_shown,
			debug=debug,
		)
		for_you_posts = await self._get_for_you_posts(
			user_id=user_id,
			preferred_category_ids=preferred_category_ids,
			affinity_by_category=affinity_by_category,
			lat=lat,
			lng=lng,
			limit=page_size,
		)

		image_map = await QuestRepository(self.db).get_top_post_images_for_quests(
			quest_ids=[candidate.quest.id for candidate in scored],
			since=datetime.now(timezone.utc) - timedelta(days=7),
		)
		quest_sections = self._build_quest_sections(
			scored=scored,
			page_size=page_size,
			debug=debug,
			image_map=image_map,
		)
		for_you_section = RecommendationSection(
			key=RecommendationSectionKey.RECOMMENDED_FOR_YOU,
			title=SECTION_TITLES[RecommendationSectionKey.RECOMMENDED_FOR_YOU],
			item_type="post",
			items=for_you_posts,
		)
		sections = [for_you_section, *quest_sections]

		explore_quests = self._items_for_quest_section(quest_sections, RecommendationSectionKey.EXPLORE_NEW_THINGS)

		return RecommendationListResponse(
			request_id=request_id,
			sections=sections,
			for_you_posts=for_you_posts,
			explore_quests=explore_quests,
			recommended_for_you=for_you_posts,
			trending_near_you=self._items_for_quest_section(quest_sections, RecommendationSectionKey.TRENDING_NEAR_YOU),
			continue_your_missions=self._items_for_quest_section(quest_sections, RecommendationSectionKey.CONTINUE_YOUR_MISSIONS),
			explore_new_things=explore_quests,
		)

	async def log_event(self, *, user_id: uuid.UUID, payload: RecommendationEventRequest) -> None:
		event = payload.event.value
		score = payload.final_score if payload.final_score is not None else payload.score
		if score is None:
			score = EVENT_SCORE_WEIGHTS.get(event)
		self.db.add(
			RecommendationLog(
				user_id=user_id,
				quest_id=payload.quest_id,
				post_id=payload.post_id,
				event=event,
				score=score,
				rank=payload.rank if payload.rank is not None else 0,
				request_id=payload.request_id,
				algorithm_version=ALGORITHM_VERSION,
			)
		)
		await self.db.commit()

	async def log_completed_event(self, *, user_id: uuid.UUID, quest_id: uuid.UUID) -> None:
		self.db.add(
			RecommendationLog(
				user_id=user_id,
				quest_id=quest_id,
				event="completed",
				score=EVENT_SCORE_WEIGHTS["completed"],
				rank=0,
				request_id=uuid.uuid4(),
				algorithm_version=ALGORITHM_VERSION,
			)
		)
		await self.db.commit()

	async def _generate_candidates(
		self,
		*,
		user_id: uuid.UUID,
		preferred_category_ids: set[int],
		status_map: dict[tuple[uuid.UUID, uuid.UUID | None], UserQuestStatus],
		popularity_by_quest: dict[uuid.UUID, float],
		lat: float | None,
		lng: float | None,
	) -> dict[tuple[uuid.UUID, uuid.UUID | None], CandidateScore]:
		rows = await self.db.scalars(
			select(Quest)
			.options(selectinload(Quest.categories))
			.where(Quest.is_active.is_(True))
			.order_by(Quest.created_at.desc())
			.limit(250)
		)
		nearby_pois = await self._get_nearby_pois(lat=lat, lng=lng) if lat is not None and lng is not None else []
		nearby_distance_by_poi = {poi.id: self._distance_m(lat, lng, poi.latitude, poi.longitude) for poi in nearby_pois} if lat is not None and lng is not None else {}

		candidates: dict[tuple[uuid.UUID, uuid.UUID | None], CandidateScore] = {}
		for quest in rows.all():
			pois_for_quest: list[Poi | None] = nearby_pois if quest.location_required and nearby_pois else [None]
			for poi in pois_for_quest:
				poi_id = poi.id if poi else None
				status = status_map.get((quest.id, poi_id), UserQuestStatus.NOT_STARTED)
				score = CandidateScore(quest=quest, status=status, poi=poi)
				self._populate_base_sources(
					score=score,
					preferred_category_ids=preferred_category_ids,
					popularity_by_quest=popularity_by_quest,
				)
				if poi is not None:
					score.sources.add("nearby")
					score.nearby_distance_m = round(nearby_distance_by_poi.get(poi.id, 0.0), 1)
				if not score.sources:
					score.sources.add("exploration")
				candidates[(quest.id, poi_id)] = score

		for (quest_id, poi_id), status in status_map.items():
			if status != UserQuestStatus.STARTED or (quest_id, poi_id) in candidates:
				continue
			quest = await self.db.scalar(
				select(Quest).options(selectinload(Quest.categories)).where(Quest.id == quest_id)
			)
			if quest is not None and quest.is_active:
				instance = await self.db.scalar(
					select(QuestInstance)
					.options(selectinload(QuestInstance.poi))
					.where(QuestInstance.user_id == user_id, QuestInstance.quest_id == quest_id)
					.order_by(QuestInstance.created_at.desc())
					.limit(1)
				)
				candidates[(quest.id, instance.poi_id if instance else None)] = CandidateScore(
					quest=quest,
					status=status,
					poi=instance.poi if instance else None,
					sources={"continue"},
				)

		return candidates

	async def _get_nearby_pois(self, *, lat: float, lng: float, radius_m: float = 5000.0) -> list[Poi]:
		lat_min, lat_max, lng_min, lng_max = self._bbox(lat, lng, radius_m)
		rows = await self.db.scalars(
			select(Poi)
			.where(
				Poi.is_active.is_(True),
				Poi.latitude >= lat_min,
				Poi.latitude <= lat_max,
				Poi.longitude >= lng_min,
				Poi.longitude <= lng_max,
			)
			.limit(50)
		)
		pois = list(rows.all())
		pois.sort(key=lambda poi: self._distance_m(lat, lng, poi.latitude, poi.longitude))
		return [
			poi
			for poi in pois
			if self._distance_m(lat, lng, poi.latitude, poi.longitude) <= max(float(poi.radius_m or 0), radius_m)
		][:10]

	def _populate_base_sources(
		self,
		*,
		score: CandidateScore,
		preferred_category_ids: set[int],
		popularity_by_quest: dict[uuid.UUID, float],
	) -> None:
		quest = score.quest
		if score.status == UserQuestStatus.STARTED:
			score.sources.add("continue")
		if preferred_category_ids.intersection({category.id for category in quest.categories}):
			score.sources.add("interest")
		if quest.id in popularity_by_quest:
			score.sources.add("trending")
		if self._freshness_score(quest.created_at) > 0:
			score.sources.add("recent")

	def _score_candidates(
		self,
		*,
		candidates: dict[tuple[uuid.UUID, uuid.UUID | None], CandidateScore],
		preferred_category_ids: set[int],
		status_map: dict[tuple[uuid.UUID, uuid.UUID | None], UserQuestStatus],
		affinity_by_category: dict[int, float],
		popularity_by_quest: dict[uuid.UUID, float],
		recently_shown: set[uuid.UUID],
		debug: bool,
	) -> list[CandidateScore]:
		scored: list[CandidateScore] = []
		for candidate in candidates.values():
			quest = candidate.quest
			if candidate.status in {UserQuestStatus.SUBMITTED, UserQuestStatus.APPROVED}:
				continue

			category_ids = {category.id for category in quest.categories}
			category_names = {category.id: category.name for category in quest.categories}
			matched_ids = preferred_category_ids.intersection(category_ids)
			if matched_ids:
				candidate.breakdown.interest = 30.0
				candidate.matched_categories = [category_names[category_id] for category_id in matched_ids]
				names = ", ".join(candidate.matched_categories)
				candidate.reasons.append(f"Based on {names} interest")

			if candidate.status == UserQuestStatus.STARTED:
				candidate.breakdown.continue_score = 35.0
				candidate.reasons.append("Continue your unfinished mission")

			if candidate.nearby_distance_m is not None:
				candidate.breakdown.nearby = 15.0
				candidate.reasons.append("Popular nearby")

			popularity = popularity_by_quest.get(quest.id, 0.0)
			candidate.popularity_score = popularity
			if popularity > 0:
				candidate.breakdown.trending = min(20.0, 10.0 + popularity)
				candidate.reasons.append("Trending with other explorers")

			affinity = sum(affinity_by_category.get(category_id, 0.0) for category_id in category_ids)
			candidate.affinity_score = affinity
			if affinity > 0:
				candidate.breakdown.affinity = min(20.0, affinity)
				candidate.reasons.append("Matches categories you complete often")

			freshness = self._freshness_score(quest.created_at)
			if freshness > 0:
				candidate.breakdown.freshness = freshness
				candidate.reasons.append("Fresh quest")

			if "exploration" in candidate.sources:
				candidate.breakdown.exploration = 5.0
				candidate.reasons.append("Explore something new")

			if quest.id in recently_shown:
				candidate.was_recently_shown = True
				candidate.breakdown.anti_repeat = -20.0
				candidate.reasons.append("Shown recently, ranked lower")

			if not candidate.reasons:
				candidate.reasons.append("Good all-around quest for today")

			scored.append(candidate)

		scored.sort(key=lambda row: row.final_score, reverse=True)
		return self._apply_diversity(scored)

	def _build_quest_sections(
		self,
		*,
		scored: list[CandidateScore],
		page_size: int,
		debug: bool,
		image_map: dict[uuid.UUID, str],
	) -> list[RecommendationSection]:
		limit = min(max(page_size, 4), 20)
		section_candidates = {
			RecommendationSectionKey.RECOMMENDED_FOR_YOU: scored,
			RecommendationSectionKey.TRENDING_NEAR_YOU: [
				row for row in scored if "nearby" in row.sources or "trending" in row.sources
			],
			RecommendationSectionKey.CONTINUE_YOUR_MISSIONS: [
				row for row in scored if row.status == UserQuestStatus.STARTED
			],
			RecommendationSectionKey.EXPLORE_NEW_THINGS: [
				row for row in scored if "interest" in row.sources
			]
			+ [
				row for row in scored if "interest" not in row.sources
			],
		}
		sections: list[RecommendationSection] = []
		for key, candidates in section_candidates.items():
			items = [
				self._to_item(
					row,
					debug=debug,
					image_url=image_map.get(row.quest.id) or row.quest.image_url,
				)
				for row in candidates[:limit]
			]
			sections.append(RecommendationSection(key=key, title=SECTION_TITLES[key], item_type="quest", items=items))
		return sections

	def _to_item(
		self,
		candidate: CandidateScore,
		*,
		debug: bool,
		image_url: str | None,
	) -> RecommendationQuestItem:
		quest = candidate.quest
		debug_info = None
		if debug:
			debug_info = RecommendationDebugInfo(
				sources=sorted(candidate.sources),
				matched_categories=candidate.matched_categories,
				nearby_distance_m=candidate.nearby_distance_m,
				poi_id=candidate.poi.id if candidate.poi else None,
				poi_name=candidate.poi.name if candidate.poi else None,
				popularity_score=candidate.popularity_score,
				affinity_score=candidate.affinity_score,
				was_recently_shown=candidate.was_recently_shown,
				rank_notes=[
					f"{name}={value}"
					for name, value in candidate.breakdown.model_dump(by_alias=True).items()
					if value != 0
				],
			)
		return RecommendationQuestItem(
			id=quest.id,
			rendered_text=render_quest_text(quest.template, quest.labels, candidate.poi.name if candidate.poi else None),
			title=quest.title,
			description=quest.description,
			difficulty=quest.difficulty.value if hasattr(quest.difficulty, "value") else str(quest.difficulty),
			image_url=image_url,
			poi_id=candidate.poi.id if candidate.poi else None,
			poi_name=candidate.poi.name if candidate.poi else None,
			nearby_distance_m=candidate.nearby_distance_m,
			labels=quest.labels or [],
			min_confidence=float(quest.min_confidence or 0.5),
			xp_reward=quest.xp_reward,
			user_status=candidate.status,
			final_score=candidate.final_score,
			reasons=candidate.reasons,
			score_breakdown=candidate.breakdown,
			debug=debug_info,
		)


	async def _log_shown_events(
		self,
		*,
		user_id: uuid.UUID,
		request_id: uuid.UUID,
		sections: list[RecommendationSection],
	) -> None:
		seen_quest_ids: set[uuid.UUID] = set()
		for section in sections:
			for index, item in enumerate(section.items, start=1):
				if not isinstance(item, RecommendationQuestItem):
					continue
				if item.id in seen_quest_ids:
					continue
				seen_quest_ids.add(item.id)
				self.db.add(
					RecommendationLog(
						user_id=user_id,
						quest_id=item.id,
						event="shown",
						score=item.final_score,
						rank=index,
						request_id=request_id,
						algorithm_version=ALGORITHM_VERSION,
					)
				)
		await self.db.commit()

	async def _get_for_you_posts(
		self,
		*,
		user_id: uuid.UUID,
		preferred_category_ids: set[int],
		affinity_by_category: dict[int, float],
		lat: float | None,
		lng: float | None,
		limit: int,
	) -> list[RecommendationPostItem]:
		normalized_limit = min(max(limit, 4), 30)
		post_quest_id = func.coalesce(Post.quest_id, UserQuest.quest_id)
		post_poi_id = func.coalesce(Submission.poi_id, UserQuest.poi_id)
		recommended_filter = self._recommended_post_filter(
			user_id=user_id,
			preferred_category_ids=preferred_category_ids,
			post_quest_id=post_quest_id,
		)
		base_query = (
			select(Post)
			.join(User, Post.user_id == User.id)
			.outerjoin(Submission, Post.submission_id == Submission.id)
			.outerjoin(UserQuest, Submission.user_quest_id == UserQuest.id)
			.outerjoin(
				QuestInstance,
				and_(
					QuestInstance.user_id == Post.user_id,
					QuestInstance.quest_id == post_quest_id,
					or_(
						QuestInstance.poi_id == post_poi_id,
						post_poi_id.is_(None),
					),
				),
			)
			.options(
				selectinload(Post.user),
				selectinload(Post.quest).selectinload(Quest.categories),
				selectinload(Post.submission).selectinload(Submission.poi),
				selectinload(Post.submission)
				.selectinload(Submission.user_quest)
				.selectinload(UserQuest.quest)
				.selectinload(Quest.categories),
			)
		)
		ranked_order = (
			(
				(Post.like_count * 3)
				+ (Post.comment_count * 5)
				+ (User.streak_days * 2)
				+ (User.xp * 0.01)
			).desc(),
			Post.created_at.desc(),
		)
		recommended_rows = await self.db.scalars(
			base_query
			.where(recommended_filter)
			.order_by(
				*ranked_order,
			)
			.limit(100)
		)
		recommended_posts = recommended_rows.unique().all()
		discovery_rows = await self.db.scalars(
			base_query
			.where(not_(recommended_filter))
			.order_by(
				Post.created_at.desc(),
				*ranked_order,
			)
			.limit(100)
		)
		discovery_posts = discovery_rows.unique().all()
		if len(discovery_posts) < self._discovery_post_target(normalized_limit):
			fallback_rows = await self.db.scalars(
				base_query
				.order_by(
					Post.created_at.desc(),
					*ranked_order,
				)
				.limit(100)
			)
			discovery_posts = self._dedupe_posts([*discovery_posts, *fallback_rows.unique().all()])

		all_posts = self._dedupe_posts([*recommended_posts, *discovery_posts])
		post_ids = [post.id for post in all_posts]
		post_counts = await self._get_post_counts(post_ids=post_ids)
		liked_post_ids = await self._get_liked_post_ids(user_id=user_id, post_ids=post_ids)
		following_ids = await self._get_following_ids(user_id=user_id)

		recommended_items = [
			self._to_post_item(
				post,
				viewer_id=user_id,
				preferred_category_ids=preferred_category_ids,
				affinity_by_category=affinity_by_category,
				lat=lat,
				lng=lng,
				counts=post_counts.get(post.id),
				liked_by_me=post.id in liked_post_ids,
				followed_by_me=post.user_id in following_ids,
			)
			for post in recommended_posts
		]
		discovery_items = [
			self._to_post_item(
				post,
				viewer_id=user_id,
				preferred_category_ids=preferred_category_ids,
				affinity_by_category=affinity_by_category,
				lat=lat,
				lng=lng,
				discovery=True,
				counts=post_counts.get(post.id),
				liked_by_me=post.id in liked_post_ids,
				followed_by_me=post.user_id in following_ids,
			)
			for post in discovery_posts
		]
		recommended_items.sort(key=lambda item: item.final_score, reverse=True)
		return self._mix_for_you_posts(
			recommended_items=recommended_items,
			discovery_items=discovery_items,
			limit=normalized_limit,
		)

	def _recommended_post_filter(
		self,
		*,
		user_id: uuid.UUID,
		preferred_category_ids: set[int],
		post_quest_id,
	):
		recommended_conditions = [
			Post.user_id == user_id,
			QuestInstance.user_id.is_not(None),
		]
		if preferred_category_ids:
			recommended_conditions.append(
				exists(
					select(1).where(
						QuestCategory.quest_id == post_quest_id,
						QuestCategory.category_id.in_(preferred_category_ids),
					)
				)
			)
		return or_(*recommended_conditions)

	@staticmethod
	def _discovery_post_target(limit: int) -> int:
		return max(1, limit - math.ceil(limit * 0.7))

	@staticmethod
	def _dedupe_posts(posts: list[Post]) -> list[Post]:
		seen: set[uuid.UUID] = set()
		deduped: list[Post] = []
		for post in posts:
			if post.id in seen:
				continue
			seen.add(post.id)
			deduped.append(post)
		return deduped

	async def _get_liked_post_ids(self, *, user_id: uuid.UUID, post_ids: list[uuid.UUID]) -> set[uuid.UUID]:
		if not post_ids:
			return set()
		rows = await self.db.execute(
			select(Like.post_id).where(Like.user_id == user_id, Like.post_id.in_(post_ids))
		)
		return {post_id for (post_id,) in rows.all()}

	async def _get_following_ids(self, *, user_id: uuid.UUID) -> set[uuid.UUID]:
		rows = await self.db.execute(
			select(Follow.following_id).where(Follow.follower_id == user_id)
		)
		return {user_id for (user_id,) in rows.all()}

	async def _get_post_counts(self, *, post_ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple[int, int]]:
		if not post_ids:
			return {}
		like_rows = await self.db.execute(
			select(Like.post_id, func.count().label("count"))
			.where(Like.post_id.in_(post_ids))
			.group_by(Like.post_id)
		)
		comment_rows = await self.db.execute(
			select(Comment.post_id, func.count().label("count"))
			.where(Comment.post_id.in_(post_ids), Comment.is_deleted.is_(False))
			.group_by(Comment.post_id)
		)
		counts = {post_id: [0, 0] for post_id in post_ids}
		for post_id, count in like_rows.all():
			counts[post_id][0] = int(count or 0)
		for post_id, count in comment_rows.all():
			counts[post_id][1] = int(count or 0)
		return {post_id: (values[0], values[1]) for post_id, values in counts.items()}

	def _mix_for_you_posts(
		self,
		*,
		recommended_items: list[RecommendationPostItem],
		discovery_items: list[RecommendationPostItem],
		limit: int,
	) -> list[RecommendationPostItem]:
		recommended_target = min(len(recommended_items), math.ceil(limit * 0.7))
		discovery_target = min(len(discovery_items), limit - recommended_target)
		if discovery_target < self._discovery_post_target(limit):
			recommended_target = min(len(recommended_items), limit - discovery_target)
		if recommended_target < math.ceil(limit * 0.7):
			discovery_target = min(len(discovery_items), limit - recommended_target)

		output: list[RecommendationPostItem] = []
		used_ids: set[uuid.UUID] = set()
		recommended_index = 0
		discovery_index = 0

		def add_next(source: list[RecommendationPostItem], start_index: int) -> int:
			index = start_index
			while index < len(source):
				item = source[index]
				index += 1
				if item.id in used_ids:
					continue
				used_ids.add(item.id)
				output.append(item)
				break
			return index

		while len(output) < limit and (
			recommended_index < len(recommended_items) or discovery_index < len(discovery_items)
		):
			slot = len(output) + 1
			discovery_due = (
				discovery_index < discovery_target
				and slot >= math.ceil(((discovery_index + 1) * limit) / max(discovery_target, 1))
			)
			if discovery_due:
				before = len(output)
				discovery_index = add_next(discovery_items, discovery_index)
				if len(output) > before:
					continue

			if recommended_index < recommended_target:
				before = len(output)
				recommended_index = add_next(recommended_items, recommended_index)
				if len(output) > before:
					continue

			if discovery_index < len(discovery_items):
				discovery_index = add_next(discovery_items, discovery_index)
			elif recommended_index < len(recommended_items):
				recommended_index = add_next(recommended_items, recommended_index)

		return output[:limit]

	def _to_post_item(
		self,
		post: Post,
		*,
		viewer_id: uuid.UUID,
		preferred_category_ids: set[int],
		affinity_by_category: dict[int, float],
		lat: float | None,
		lng: float | None,
		discovery: bool = False,
		counts: tuple[int, int] | None = None,
		liked_by_me: bool = False,
		followed_by_me: bool = False,
	) -> RecommendationPostItem:
		submission_image_url = post.image_url or (post.submission.image_url if post.submission else None)
		submission_poi_name = post.submission.poi.name if post.submission and post.submission.poi else None
		submission_poi_id = post.submission.poi_id if post.submission else None
		user_quest_poi_id = (
			post.submission.user_quest.poi_id
			if post.submission and post.submission.user_quest
			else None
		)
		quest_info = None
		quest = None
		if post.submission and post.submission.user_quest and post.submission.user_quest.quest:
			quest = post.submission.user_quest.quest
			quest_info = PostQuestInfo(
				id=quest.id,
				poi_id=submission_poi_id or user_quest_poi_id,
				title=quest.title,
				description=quest.description,
				xp_reward=quest.xp_reward,
				poi_name=submission_poi_name,
			)
		elif post.quest:
			quest = post.quest
			quest_info = PostQuestInfo(
				id=quest.id,
				poi_id=None,
				title=quest.title,
				description=quest.description,
				xp_reward=quest.xp_reward,
				poi_name=submission_poi_name,
			)

		reasons = ["Discovery post"] if discovery else ["Relevant post"]
		score = 0.0
		if post.user_id == viewer_id:
			score += 10.0
			reasons.append("Your post")
		if quest is not None:
			category_ids = {category.id for category in quest.categories}
			matched_ids = preferred_category_ids.intersection(category_ids)
			if matched_ids:
				score += 30.0
				reasons.append("Matches your interests")
			affinity_score = min(20.0, sum(affinity_by_category.get(category_id, 0.0) for category_id in category_ids))
			if affinity_score > 0:
				score += affinity_score
				reasons.append("Matches quests you often complete")

		if lat is not None and lng is not None and post.submission and post.submission.poi:
			distance_m = self._distance_m(lat, lng, post.submission.poi.latitude, post.submission.poi.longitude)
			if distance_m <= max(float(post.submission.poi.radius_m or 0), 5000.0):
				score += 15.0
				reasons.append("Near your current area")

		engagement_score = min(25.0, float(post.like_count * 3) + float(post.comment_count * 5))
		if engagement_score > 0:
			score += engagement_score
			reasons.append("High community engagement")

		creator_score = min(15.0, float((post.user.streak_days or 0) * 2) + float((post.user.xp or 0) * 0.01))
		if creator_score > 0:
			score += creator_score
			reasons.append("Active creator")

		freshness_score = self._freshness_score(post.created_at)
		if freshness_score > 0:
			score += freshness_score
			reasons.append("Fresh post")

		like_count, comment_count = counts if counts is not None else (post.like_count, post.comment_count)
		return RecommendationPostItem(
			id=post.id,
			submission_id=post.submission_id,
			submission_image_url=submission_image_url,
			caption=post.caption,
			location_name=post.location_name,
			quest=quest_info,
			user=UserPublicResponse.model_validate(post.user),
			like_count=like_count,
			comment_count=comment_count,
			liked_by_me=liked_by_me,
			followed_by_me=followed_by_me,
			created_at=post.created_at,
			final_score=round(score, 3),
			reasons=reasons,
		)

	async def _get_user_status_map(self, *, user_id: uuid.UUID) -> dict[tuple[uuid.UUID, uuid.UUID | None], UserQuestStatus]:
		rows = await self.db.execute(
			select(UserQuest.quest_id, UserQuest.poi_id, UserQuest.status).where(UserQuest.user_id == user_id)
		)
		return {(quest_id, poi_id): status for quest_id, poi_id, status in rows.all()}

	async def _get_recently_shown(self, *, user_id: uuid.UUID) -> set[uuid.UUID]:
		cutoff = datetime.now(timezone.utc) - timedelta(days=7)
		rows = await self.db.execute(
			select(RecommendationLog.quest_id).where(
				RecommendationLog.user_id == user_id,
				RecommendationLog.quest_id.is_not(None),
				RecommendationLog.event == "shown",
				RecommendationLog.created_at >= cutoff,
			)
		)
		return {quest_id for (quest_id,) in rows.all()}

	async def _get_category_affinity(self, *, user_id: uuid.UUID) -> dict[int, float]:
		rows = await self.db.scalars(
			select(Quest)
			.join(UserQuest, UserQuest.quest_id == Quest.id)
			.where(UserQuest.user_id == user_id, UserQuest.status.in_([UserQuestStatus.STARTED, UserQuestStatus.APPROVED]))
			.options(selectinload(Quest.categories))
		)
		affinity: dict[int, float] = {}
		for quest in rows.all():
			for category in quest.categories:
				affinity[category.id] = affinity.get(category.id, 0.0) + 5.0
		return affinity

	async def _get_popularity_scores(self) -> dict[uuid.UUID, float]:
		scores: dict[uuid.UUID, float] = {}
		cutoff = datetime.now(timezone.utc) - timedelta(days=14)
		log_rows = await self.db.execute(
			select(
				RecommendationLog.quest_id,
				func.sum(case((RecommendationLog.event == "clicked", 2), else_=0)).label("clicks"),
				func.sum(case((RecommendationLog.event == "started", 4), else_=0)).label("starts"),
				func.sum(case((RecommendationLog.event == "completed", 6), else_=0)).label("completed"),
				func.sum(case((RecommendationLog.event == "post_liked", 1), else_=0)).label("post_likes"),
				func.sum(case((RecommendationLog.event == "post_commented", 3), else_=0)).label("post_comments"),
			)
			.where(RecommendationLog.created_at >= cutoff, RecommendationLog.quest_id.is_not(None))
			.group_by(RecommendationLog.quest_id)
		)
		for quest_id, clicks, starts, completed, post_likes, post_comments in log_rows.all():
			score = float((clicks or 0) + (starts or 0) + (completed or 0) + (post_likes or 0) + (post_comments or 0))
			if score > 0:
				scores[quest_id] = score

		post_rows = await self.db.execute(
			select(Post.quest_id, func.count().label("count")).where(Post.quest_id.is_not(None)).group_by(Post.quest_id)
		)
		for quest_id, count in post_rows.all():
			if quest_id is not None:
				scores[quest_id] = scores.get(quest_id, 0.0) + float(count or 0)
		return scores

	@staticmethod
	def _items_for_quest_section(
		sections: list[RecommendationSection],
		key: RecommendationSectionKey,
	) -> list[RecommendationQuestItem]:
		for section in sections:
			if section.key == key:
				return [item for item in section.items if isinstance(item, RecommendationQuestItem)]
		return []

	@staticmethod
	def _normalize_category_ids(raw_ids: list[int] | list[str] | None) -> set[int]:
		normalized: set[int] = set()
		for item in raw_ids or []:
			try:
				normalized.add(int(item))
			except (TypeError, ValueError):
				continue
		return normalized

	@staticmethod
	def _freshness_score(created_at: datetime | None) -> float:
		if not created_at:
			return 0.0
		if created_at.tzinfo is None:
			created_at = created_at.replace(tzinfo=timezone.utc)
		age_days = max((datetime.now(timezone.utc) - created_at).days, 0)
		if age_days <= 7:
			return 8.0
		if age_days <= 30:
			return 3.0
		return 0.0

	@staticmethod
	def _distance_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
		radius_m = 6371000
		phi1 = math.radians(lat1)
		phi2 = math.radians(lat2)
		delta_phi = math.radians(lat2 - lat1)
		delta_lambda = math.radians(lng2 - lng1)
		a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
		return radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

	@staticmethod
	def _bbox(lat: float, lng: float, radius_m: float) -> tuple[float, float, float, float]:
		lat_delta = radius_m / 111000.0
		lng_delta = radius_m / (111000.0 * max(0.1, math.cos(math.radians(lat))))
		return (lat - lat_delta, lat + lat_delta, lng - lng_delta, lng + lng_delta)

	@staticmethod
	def _apply_diversity(scored: list[CandidateScore]) -> list[CandidateScore]:
		category_counts: dict[int, int] = {}
		diversified: list[CandidateScore] = []
		remaining: list[CandidateScore] = []
		for candidate in scored:
			category_ids = [category.id for category in candidate.quest.categories]
			if not category_ids or any(category_counts.get(category_id, 0) < 3 for category_id in category_ids):
				diversified.append(candidate)
				for category_id in category_ids:
					category_counts[category_id] = category_counts.get(category_id, 0) + 1
			else:
				remaining.append(candidate)
		return diversified + remaining
