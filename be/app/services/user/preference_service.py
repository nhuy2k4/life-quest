import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.redis import get_redis_client
from app.models.quest import Category
from app.models.user import User
from app.models.user_preference import UserPreference
from app.schemas.preference import PreferenceRequest


class PreferenceService:
	"""Business logic for user preference operations."""

	VALID_ACTIVITY_LEVELS = {"low", "medium", "high"}
	DEFAULT_INTEREST_WEIGHT = 1.0

	def __init__(self, db: AsyncSession):
		self.db = db

	async def get_my_preferences(self, user_id: uuid.UUID) -> UserPreference:
		preference = await self.db.scalar(
			select(UserPreference).where(UserPreference.user_id == user_id)
		)
		if preference is None:
			raise NotFoundException("Chua co preferences cho user nay")
		return preference

	async def update_my_preferences(self, user_id: uuid.UUID, payload: PreferenceRequest) -> UserPreference:
		activity_level = payload.activity_level.strip().lower()
		if activity_level not in self.VALID_ACTIVITY_LEVELS:
			raise BadRequestException("activity_level phai la low, medium hoac high")

		user = await self.db.scalar(select(User).where(User.id == user_id))
		if user is None:
			raise NotFoundException("User khong ton tai")

		interest_ids = self._normalize_interest_ids(payload.interests)
		if interest_ids:
			existing_ids = set(await self.db.scalars(select(Category.id).where(Category.id.in_(interest_ids))))
			missing_ids = sorted(set(interest_ids) - existing_ids)
			if missing_ids:
				raise BadRequestException(f"Category id khong hop le: {missing_ids}")

		preference = await self.db.scalar(
			select(UserPreference).where(UserPreference.user_id == user_id)
		)
		if preference is None:
			preference = UserPreference(user_id=user_id)
			self.db.add(preference)

		preference.interests = interest_ids
		preference.interest_weights = self._fixed_interest_weights(interest_ids)
		preference.activity_level = activity_level
		preference.location_enabled = payload.location_enabled

		user.onboarding_completed = True

		await self.db.commit()
		await self.db.refresh(preference)

		await self.invalidate_cache(str(user_id))
		return preference

	async def invalidate_cache(self, user_id: str) -> None:
		"""Hook for recommendation cache invalidation."""
		try:
			client = await get_redis_client()
			keys = await client.keys(f"recommendations:user:{user_id}:*")
			if keys:
				await client.delete(*keys)
		except Exception:
			return

	@classmethod
	def _fixed_interest_weights(cls, interest_ids: list[int]) -> dict[str, float]:
		return {str(category_id): cls.DEFAULT_INTEREST_WEIGHT for category_id in interest_ids}

	@staticmethod
	def _normalize_interest_ids(interests: list[int]) -> list[int]:
		seen: set[int] = set()
		normalized: list[int] = []
		for item in interests:
			category_id = int(item)
			if category_id <= 0 or category_id in seen:
				continue
			seen.add(category_id)
			normalized.append(category_id)
		return normalized
