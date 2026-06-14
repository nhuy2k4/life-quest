from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.badge import Badge
from app.models.enums import EventStatus, SubmissionStatus, XpSource
from app.models.event import Event, EventQuest, EventResult
from app.models.quest import Quest
from app.models.social import Post
from app.models.submission import Submission
from app.models.user import User
from app.models.user_quest import UserQuest
from app.models.xp_transaction import XpTransaction
from app.schemas.event import (
	EventActionResponse,
	EventCreateRequest,
	EventDetailResponse,
	EventLeaderboardItem,
	EventLeaderboardPost,
	EventLeaderboardResponse,
	EventListItem,
	EventRewardTier,
	EventUpdateRequest,
)
from app.schemas.social import PostResponse
from app.schemas.user import UserPublicResponse
from app.services.gamification.badge_service import BadgeService
from app.services.notification.notification_service import NotificationService
from app.services.social.social_service import SocialService


class EventService:
	def __init__(self, db: AsyncSession) -> None:
		self.db = db
		self.social_service = SocialService(db)

	async def list_events(self, *, status: str | None = None) -> list[EventListItem]:
		await self._finalize_overdue_events()
		stmt = select(Event)
		now = datetime.now(timezone.utc)

		if status == EventStatus.ACTIVE:
			stmt = stmt.where(
				Event.status == EventStatus.ACTIVE,
				Event.start_at <= now,
				Event.end_at >= now,
			)
		elif status == EventStatus.ENDED:
			stmt = stmt.where(Event.status == EventStatus.ENDED)
		elif status == EventStatus.DRAFT:
			stmt = stmt.where(Event.status == EventStatus.DRAFT)

		stmt = stmt.order_by(Event.start_at.desc())
		rows = await self.db.scalars(stmt)
		return [EventListItem.model_validate(item) for item in rows.all()]

	async def _finalize_overdue_events(self) -> None:
		now = datetime.now(timezone.utc)
		event_ids = await self.db.scalars(
			select(Event.id).where(
				Event.status == EventStatus.ACTIVE,
				Event.end_at <= now,
			)
		)
		for event_id in event_ids.all():
			await self._finalize_if_needed(event_id=event_id)

	async def get_event_detail(self, *, event_id: uuid.UUID) -> EventDetailResponse:
		await self._finalize_if_needed(event_id=event_id)
		event = await self.db.scalar(
			select(Event)
			.options(selectinload(Event.quests))
			.where(Event.id == event_id)
		)
		if event is None:
			raise NotFoundException("Event khong ton tai")

		reward_config = self._normalize_reward_config(event.reward_config)
		return EventDetailResponse(
			id=event.id,
			title=event.title,
			description=event.description,
			banner_url=event.banner_url,
			start_at=event.start_at,
			end_at=event.end_at,
			status=event.status,
			reward_config=reward_config,
			quests=[
				{
					"id": quest.id,
					"title": quest.title,
					"description": quest.description,
					"xp_reward": quest.xp_reward,
				}
				for quest in event.quests
			],
		)

	async def create_event(self, *, actor_id: uuid.UUID, payload: EventCreateRequest) -> EventDetailResponse:
		self._validate_event_window(payload.start_at, payload.end_at)
		self._validate_single_quest(payload.quest_ids)

		quests = await self._get_quests(payload.quest_ids)
		if len(quests) != len(set(payload.quest_ids)):
			raise NotFoundException("Quest khong ton tai")

		reward_config = self._serialize_reward_config(payload.reward_config)
		status = EventStatus(payload.status or EventStatus.DRAFT)

		event = Event(
			title=payload.title,
			description=payload.description,
			banner_url=payload.banner_url,
			start_at=payload.start_at,
			end_at=payload.end_at,
			status=status,
			reward_config=reward_config,
			created_by=actor_id,
		)
		self.db.add(event)
		await self.db.flush()

		await self._set_event_quests(event_id=event.id, quest_ids=payload.quest_ids)
		await self.db.commit()

		return await self.get_event_detail(event_id=event.id)

	async def update_event(self, *, event_id: uuid.UUID, payload: EventUpdateRequest) -> EventDetailResponse:
		event = await self.db.scalar(select(Event).where(Event.id == event_id))
		if event is None:
			raise NotFoundException("Event khong ton tai")

		start_at = payload.start_at or event.start_at
		end_at = payload.end_at or event.end_at
		self._validate_event_window(start_at, end_at)

		if payload.title is not None:
			event.title = payload.title
		if payload.description is not None:
			event.description = payload.description
		if payload.banner_url is not None:
			event.banner_url = payload.banner_url
		if payload.start_at is not None:
			event.start_at = payload.start_at
		if payload.end_at is not None:
			event.end_at = payload.end_at
		if payload.status is not None:
			event.status = EventStatus(payload.status)
		if payload.reward_config is not None:
			event.reward_config = self._serialize_reward_config(payload.reward_config)

		if payload.quest_ids is not None:
			self._validate_single_quest(payload.quest_ids)
			quests = await self._get_quests(payload.quest_ids)
			if len(quests) != len(set(payload.quest_ids)):
				raise NotFoundException("Quest khong ton tai")
			await self._set_event_quests(event_id=event.id, quest_ids=payload.quest_ids)

		await self.db.commit()
		return await self.get_event_detail(event_id=event.id)

	async def end_event(self, *, event_id: uuid.UUID) -> EventActionResponse:
		await self._finalize_if_needed(event_id=event_id, force=True)
		return EventActionResponse()

	async def list_event_posts(
		self,
		*,
		event_id: uuid.UUID,
		user_id: uuid.UUID,
		page: int,
		page_size: int,
	) -> tuple[list[PostResponse], int]:
		offset = (page - 1) * page_size
		total = await self.db.scalar(
			select(func.count())
			.select_from(Post)
			.join(Submission, Submission.id == Post.submission_id)
			.where(Post.event_id == event_id, Submission.status == SubmissionStatus.APPROVED)
		)
		rows = await self.db.scalars(
			select(Post)
			.options(
				selectinload(Post.user),
				selectinload(Post.submission).selectinload(Submission.poi),
				selectinload(Post.submission).selectinload(Submission.user_quest).selectinload(UserQuest.quest),
				selectinload(Post.quest),
				selectinload(Post.poi),
				selectinload(Post.event),
			)
			.join(Submission, Submission.id == Post.submission_id)
			.where(Post.event_id == event_id, Submission.status == SubmissionStatus.APPROVED)
			.order_by(Post.created_at.desc())
			.offset(offset)
			.limit(page_size)
		)
		posts = rows.all()

		liked_post_ids = await self.social_service._get_liked_post_ids(
			user_id=user_id,
			post_ids=[post.id for post in posts],
		)
		following_ids = await self.social_service._get_following_ids(user_id=user_id)
		counts_by_post = await self.social_service._get_post_counts(post_ids=[post.id for post in posts])

		items = [
			SocialService._to_post_response(
				post,
				liked_by_me=post.id in liked_post_ids,
				followed_by_me=post.user_id in following_ids,
				counts=counts_by_post.get(post.id),
			)
			for post in posts
		]

		return items, int(total or 0)

	async def get_leaderboard(
		self,
		*,
		event_id: uuid.UUID,
		limit: int = 5,
	) -> EventLeaderboardResponse:
		await self._finalize_if_needed(event_id=event_id)
		event = await self.db.scalar(select(Event).where(Event.id == event_id))
		if event is None:
			raise NotFoundException("Event khong ton tai")

		if event.status == EventStatus.ENDED:
			return await self._get_snapshot_leaderboard(event_id=event_id)
		return await self._get_live_leaderboard(event_id=event_id, limit=limit)

	async def _get_snapshot_leaderboard(self, *, event_id: uuid.UUID) -> EventLeaderboardResponse:
		rows = await self.db.execute(
			select(EventResult, User, Post, Submission)
			.join(User, User.id == EventResult.user_id)
			.outerjoin(Post, Post.id == EventResult.post_id)
			.outerjoin(Submission, Submission.id == Post.submission_id)
			.where(EventResult.event_id == event_id)
			.order_by(EventResult.rank.asc())
		)

		items: list[EventLeaderboardItem] = []
		for result, user, post, submission in rows.all():
			image_url = None
			if post is not None:
				image_url = post.image_url or (submission.image_url if submission else None)

			items.append(
				EventLeaderboardItem(
					rank=result.rank,
					user=UserPublicResponse.model_validate(user),
					post=EventLeaderboardPost(
						id=post.id if post else None,
						image_url=image_url,
						like_count=result.total_likes,
						is_deleted=post is None,
					),
				)
			)

		return EventLeaderboardResponse(items=items, total=len(items))

	async def _get_live_leaderboard(self, *, event_id: uuid.UUID, limit: int) -> EventLeaderboardResponse:
		ranked = (
			select(
				Post.id.label("post_id"),
				Post.user_id.label("user_id"),
				Post.like_count.label("like_count"),
				Post.created_at.label("created_at"),
				func.coalesce(Post.image_url, Submission.image_url).label("image_url"),
				func.row_number()
				.over(
					partition_by=Post.user_id,
					order_by=(Post.like_count.desc(), Post.created_at.asc(), Post.id.asc()),
				)
				.label("rank_row"),
			)
			.join(Submission, Submission.id == Post.submission_id)
			.where(Post.event_id == event_id, Submission.status == SubmissionStatus.APPROVED)
		)
		best = ranked.subquery()
		rows = await self.db.execute(
			select(best)
			.where(best.c.rank_row == 1)
			.order_by(best.c.like_count.desc(), best.c.created_at.asc(), best.c.post_id.asc())
			.limit(limit)
		)
		best_rows = rows.all()
		user_ids = [row.user_id for row in best_rows]
		if not user_ids:
			return EventLeaderboardResponse(items=[], total=0)

		user_rows = await self.db.scalars(select(User).where(User.id.in_(user_ids)))
		user_map = {user.id: user for user in user_rows.all()}

		items: list[EventLeaderboardItem] = []
		for index, row in enumerate(best_rows, start=1):
			user = user_map.get(row.user_id)
			if user is None:
				continue
			items.append(
				EventLeaderboardItem(
					rank=index,
					user=UserPublicResponse.model_validate(user),
					post=EventLeaderboardPost(
						id=row.post_id,
						image_url=row.image_url,
						like_count=int(row.like_count or 0),
						is_deleted=False,
					),
				)
			)

		return EventLeaderboardResponse(items=items, total=len(items))

	async def _finalize_if_needed(self, *, event_id: uuid.UUID, force: bool = False) -> None:
		stmt = (
			select(Event)
			.where(Event.id == event_id)
			.with_for_update()
		)
		event = await self.db.scalar(stmt)
		if event is None:
			return
		if event.status == EventStatus.ENDED:
			return

		now = datetime.now(timezone.utc)
		if not force and event.end_at > now:
			return

		await self._finalize_event(event)
		await self.db.commit()

	async def _finalize_event(self, event: Event) -> None:
		event.status = EventStatus.ENDED

		reward_config = self._normalize_reward_config(event.reward_config)
		leaderboard = await self._get_live_leaderboard(event_id=event.id, limit=5)
		badge_service = BadgeService(self.db)

		for item in leaderboard.items:
			reward = self._resolve_reward(reward_config, item.rank)
			result = EventResult(
				event_id=event.id,
				user_id=item.user.id,
				post_id=item.post.id,
				total_likes=item.post.like_count,
				rank=item.rank,
				bonus_xp=reward.bonus_xp,
				badge_id=reward.badge_id,
				awarded_at=datetime.now(timezone.utc),
			)
			self.db.add(result)

			if reward.bonus_xp > 0:
				await self._grant_event_xp(user_id=item.user.id, amount=reward.bonus_xp)

			if reward.badge_id:
				await badge_service.repo.award_badge(user_id=item.user.id, badge_id=reward.badge_id)

			await NotificationService(self.db).create_notification(
				user_id=item.user.id,
				notification_type="event_reward",
				data={
					"event_id": str(event.id),
					"rank": item.rank,
					"bonus_xp": reward.bonus_xp,
					"badge_id": str(reward.badge_id) if reward.badge_id else None,
				},
				push_title="Event reward",
				push_body=f"You placed #{item.rank} in {event.title}.",
			)

	async def _grant_event_xp(self, *, user_id: uuid.UUID, amount: int) -> None:
		user = await self.db.scalar(select(User).where(User.id == user_id))
		if user is None:
			return
		self.db.add(
			XpTransaction(
				user_id=user_id,
				amount=amount,
				source=XpSource.EVENT_REWARD,
			)
		)
		user.xp += amount

		level = await self.db.scalar(
			select(func.max(User.level_id)).select_from(User).where(User.id == user_id)
		)
		if level is not None and user.level_id != level:
			user.level_id = level

	async def _set_event_quests(self, *, event_id: uuid.UUID, quest_ids: list[uuid.UUID]) -> None:
		await self.db.execute(delete(EventQuest).where(EventQuest.event_id == event_id))
		for quest_id in quest_ids:
			self.db.add(EventQuest(event_id=event_id, quest_id=quest_id))

	async def _get_quests(self, quest_ids: list[uuid.UUID]) -> list[Quest]:
		rows = await self.db.scalars(select(Quest).where(Quest.id.in_(quest_ids)))
		return rows.all()

	@staticmethod
	def _validate_event_window(start_at: datetime, end_at: datetime) -> None:
		if end_at <= start_at:
			raise BadRequestException("Thoi gian ket thuc phai lon hon bat dau")

	@staticmethod
	def _validate_single_quest(quest_ids: list[uuid.UUID]) -> None:
		if len(quest_ids) != 1:
			raise BadRequestException("Event phai co dung 1 quest")

	@staticmethod
	def _normalize_reward_config(payload: dict | list) -> list[EventRewardTier]:
		if isinstance(payload, list):
			return [EventRewardTier.model_validate(item) for item in payload]
		if isinstance(payload, dict):
			items = payload.get("items") or []
			return [EventRewardTier.model_validate(item) for item in items]
		return []

	@staticmethod
	def _serialize_reward_config(payload: list[EventRewardTier]) -> list[dict]:
		return [
			{
				"rank_from": tier.rank_from,
				"rank_to": tier.rank_to,
				"bonus_xp": tier.bonus_xp,
				"badge_id": str(tier.badge_id) if tier.badge_id is not None else None,
			}
			for tier in payload
		]

	@staticmethod
	def _resolve_reward(config: list[EventRewardTier], rank: int) -> EventRewardTier:
		for tier in config:
			if tier.rank_from <= rank <= tier.rank_to:
				return tier
		return EventRewardTier(rank_from=rank, rank_to=rank, bonus_xp=0, badge_id=None)
