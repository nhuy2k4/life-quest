from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.badge import Badge, UserBadge
from app.models.social import Comment, Like, Post
from app.models.submission import Submission
from app.models.user import User
from app.models.user_quest import UserQuest
from app.models.event import Event
from app.models.enums import SubmissionStatus


@dataclass
class UserStats:
	"""Aggregated stats used for badge criteria evaluation."""

	quests_completed: int
	posts_created: int
	comments_created: int
	likes_received: int
	streak_days: int
	xp_total: int
	level_id: int
	approved_submissions: int
	events_participated: int


class BadgeRepository:
	def __init__(self, db: AsyncSession) -> None:
		self.db = db

	# ── Stats ────────────────────────────────────────────────────────────────

	async def get_user_stats(self, user_id: uuid.UUID) -> UserStats:
		"""Fetch all badge-relevant stats for a user in a small number of queries."""

		# User base stats
		user = await self.db.scalar(select(User).where(User.id == user_id))
		if user is None:
			return UserStats(
				quests_completed=0,
				posts_created=0,
				comments_created=0,
				likes_received=0,
				streak_days=0,
				xp_total=0,
				level_id=1,
				approved_submissions=0,
				events_participated=0,
			)

		# Quests completed
		quests_completed = await self.db.scalar(
			select(func.count())
			.select_from(UserQuest)
			.where(
				UserQuest.user_id == user_id,
				UserQuest.status == "approved",
			)
		)

		# Posts created
		posts_created = await self.db.scalar(
			select(func.count()).select_from(Post).where(Post.user_id == user_id)
		)

		# Comments created
		comments_created = await self.db.scalar(
			select(func.count()).select_from(Comment).where(Comment.user_id == user_id)
		)

		# Likes received on user's posts
		likes_received = await self.db.scalar(
			select(func.count())
			.select_from(Like)
			.join(Post, Like.post_id == Post.id)
			.where(Post.user_id == user_id)
		)

		# Approved submissions (for "Trusted Explorer" type badges)
		approved_submissions = await self.db.scalar(
			select(func.count())
			.select_from(Submission)
			.join(UserQuest, Submission.user_quest_id == UserQuest.id)
			.where(
				UserQuest.user_id == user_id,
				Submission.status == SubmissionStatus.APPROVED,
			)
		)

		# Events participated: số event khác nhau mà user có post được approve
		events_participated = await self.db.scalar(
			select(func.count(func.distinct(Post.event_id)))
			.select_from(Post)
			.join(Submission, Submission.id == Post.submission_id)
			.where(
				Post.user_id == user_id,
				Post.event_id.is_not(None),
				Submission.status == SubmissionStatus.APPROVED,
			)
		)

		return UserStats(
			quests_completed=int(quests_completed or 0),
			posts_created=int(posts_created or 0),
			comments_created=int(comments_created or 0),
			likes_received=int(likes_received or 0),
			streak_days=user.streak_days,
			xp_total=user.xp,
			level_id=user.level_id,
			approved_submissions=int(approved_submissions or 0),
			events_participated=int(events_participated or 0),
		)

	# ── Badges ───────────────────────────────────────────────────────────────

	async def get_all_active_badges(self) -> list[Badge]:
		stmt = (
			select(Badge)
			.where(Badge.is_active == True)  # noqa: E712
			.order_by(Badge.sort_order)
		)
		result = await self.db.execute(stmt)
		return list(result.scalars().all())

	async def get_user_unlocked_badge_ids(self, user_id: uuid.UUID) -> dict[uuid.UUID, UserBadge]:
		"""Return map of badge_id → UserBadge for all badges the user has unlocked."""
		stmt = select(UserBadge).where(UserBadge.user_id == user_id)
		result = await self.db.execute(stmt)
		return {ub.badge_id: ub for ub in result.scalars().all()}

	async def award_badge(self, user_id: uuid.UUID, badge_id: uuid.UUID) -> UserBadge | None:
		"""
		Award a badge to the user idempotently.
		Returns the new UserBadge if created, None if already existed.
		"""
		# Check for existing (avoids DB constraint error on concurrent requests)
		existing = await self.db.scalar(
			select(UserBadge).where(
				UserBadge.user_id == user_id,
				UserBadge.badge_id == badge_id,
			)
		)
		if existing is not None:
			return None

		ub = UserBadge(user_id=user_id, badge_id=badge_id)
		self.db.add(ub)
		await self.db.flush()
		return ub

	async def get_featured_badges(self, user_id: uuid.UUID, limit: int = 3) -> list[tuple[Badge, UserBadge]]:
		"""
		Return up to `limit` featured badges:
		Unlocked badges ordered by rarity desc, then earned_at desc.
		"""
		rarity_order = {
			"legendary": 0,
			"epic": 1,
			"rare": 2,
			"common": 3,
		}
		# Get unlocked badges with their badge info
		stmt = (
			select(UserBadge)
			.options(selectinload(UserBadge.badge))
			.where(UserBadge.user_id == user_id)
			.order_by(UserBadge.earned_at.desc())
		)
		result = await self.db.execute(stmt)
		user_badges = list(result.scalars().all())

		# Sort by rarity desc, then recency desc
		user_badges.sort(
			key=lambda ub: (rarity_order.get(ub.badge.rarity, 99), -(ub.earned_at.timestamp() if ub.earned_at else 0)),
		)

		return [(ub.badge, ub) for ub in user_badges[:limit]]
