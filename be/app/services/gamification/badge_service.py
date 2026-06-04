from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.badge import Badge, UserBadge
from app.repositories.badge_repository import BadgeRepository, UserStats
from app.schemas.badge import BadgeItem, BadgeListResponse, BadgeProgress, FeaturedBadge, FeaturedBadgeResponse


def _compute_progress(badge: Badge, stats: UserStats) -> BadgeProgress:
	"""Return current / target progress for a badge's criteria."""
	criteria = badge.criteria or {}
	criteria_type: str = criteria.get("type", "")
	target: int = int(criteria.get("target", criteria.get("count", 1)))

	current_map: dict[str, int] = {
		"quests_completed": stats.quests_completed,
		"posts_created": stats.posts_created,
		"comments_created": stats.comments_created,
		"likes_received": stats.likes_received,
		"streak_days": stats.streak_days,
		"xp_total": stats.xp_total,
		"level_reached": stats.level_id,
		"approved_submissions": stats.approved_submissions,
	}

	current = current_map.get(criteria_type, 0)
	return BadgeProgress(current=min(current, target), target=target)


def _is_criteria_met(badge: Badge, stats: UserStats) -> bool:
	"""Return True if the user meets the badge's unlock criteria."""
	progress = _compute_progress(badge, stats)
	return progress.current >= progress.target


class BadgeService:
	def __init__(self, db: AsyncSession) -> None:
		self.db = db
		self.repo = BadgeRepository(db)

	async def get_badges_for_user(
		self,
		user_id: uuid.UUID,
		category: str | None = None,
	) -> BadgeListResponse:
		"""Return all active badges enriched with user progress & unlock status."""
		badges = await self.repo.get_all_active_badges()
		unlocked_map = await self.repo.get_user_unlocked_badge_ids(user_id)
		stats = await self.repo.get_user_stats(user_id)

		items: list[BadgeItem] = []
		for badge in badges:
			if category and badge.category != category:
				continue

			user_badge: UserBadge | None = unlocked_map.get(badge.id)
			is_unlocked = user_badge is not None
			progress = _compute_progress(badge, stats)

			items.append(
				BadgeItem(
					id=badge.id,
					name=badge.name,
					description=badge.description,
					icon_url=badge.icon_url,
					rarity=badge.rarity,
					category=badge.category,
					criteria=badge.criteria,
					is_hidden=badge.is_hidden,
					is_unlocked=is_unlocked,
					unlocked_at=user_badge.earned_at if user_badge else None,
					progress=progress,
				)
			)

		return BadgeListResponse(data=items, total=len(items))

	async def get_badge_detail(self, user_id: uuid.UUID, badge_id: uuid.UUID) -> BadgeItem | None:
		"""Return a single badge with user progress."""
		from sqlalchemy import select
		from app.models.badge import Badge

		badge = await self.db.scalar(select(Badge).where(Badge.id == badge_id))
		if badge is None:
			return None

		unlocked_map = await self.repo.get_user_unlocked_badge_ids(user_id)
		stats = await self.repo.get_user_stats(user_id)

		user_badge: UserBadge | None = unlocked_map.get(badge.id)
		is_unlocked = user_badge is not None

		return BadgeItem(
			id=badge.id,
			name=badge.name,
			description=badge.description,
			icon_url=badge.icon_url,
			rarity=badge.rarity,
			category=badge.category,
			criteria=badge.criteria,
			is_hidden=badge.is_hidden,
			is_unlocked=is_unlocked,
			unlocked_at=user_badge.earned_at if user_badge else None,
			progress=_compute_progress(badge, stats),
		)

	async def get_featured_badges(self, user_id: uuid.UUID) -> FeaturedBadgeResponse:
		"""Return top featured badges for the profile header."""
		pairs = await self.repo.get_featured_badges(user_id, limit=3)
		items = [
			FeaturedBadge(
				id=badge.id,
				name=badge.name,
				icon_url=badge.icon_url,
				rarity=badge.rarity,
				unlocked_at=user_badge.earned_at,
			)
			for badge, user_badge in pairs
		]
		return FeaturedBadgeResponse(data=items)

	async def evaluate_and_award_badges(self, user_id: uuid.UUID) -> list[Badge]:
		"""
		Evaluate all badge criteria for a user and auto-award any newly earned badges.
		Called after significant events (quest approval, post creation, etc.).
		Returns list of newly awarded Badge objects.
		"""
		badges = await self.repo.get_all_active_badges()
		unlocked_map = await self.repo.get_user_unlocked_badge_ids(user_id)
		stats = await self.repo.get_user_stats(user_id)

		newly_awarded: list[Badge] = []

		for badge in badges:
			if badge.id in unlocked_map:
				# Already unlocked
				continue
			if _is_criteria_met(badge, stats):
				result = await self.repo.award_badge(user_id, badge.id)
				if result is not None:
					newly_awarded.append(badge)

		return newly_awarded
