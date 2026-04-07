import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.user import User
from app.models.user_preference import UserPreference
from app.schemas.preference import PreferenceRequest


class PreferenceService:
	"""Business logic for user preference operations."""

	VALID_ACTIVITY_LEVELS = {"low", "medium", "high"}

	def __init__(self, db: AsyncSession):
		self.db = db

	async def get_my_preferences(self, user_id: uuid.UUID) -> UserPreference:
		preference = await self.db.scalar(
			select(UserPreference).where(UserPreference.user_id == user_id)
		)
		if preference is None:
			raise NotFoundException("Chưa có preferences cho user này")
		return preference

	async def update_my_preferences(self, user_id: uuid.UUID, payload: PreferenceRequest) -> UserPreference:
		activity_level = payload.activity_level.strip().lower()
		if activity_level not in self.VALID_ACTIVITY_LEVELS:
			raise BadRequestException("activity_level phải là low, medium hoặc high")

		user = await self.db.scalar(select(User).where(User.id == user_id))
		if user is None:
			raise NotFoundException("User không tồn tại")

		preference = await self.db.scalar(
			select(UserPreference).where(UserPreference.user_id == user_id)
		)
		if preference is None:
			preference = UserPreference(user_id=user_id)
			self.db.add(preference)

		preference.interests = payload.interests
		preference.activity_level = activity_level
		preference.location_enabled = payload.location_enabled

		# User completed onboarding once preferences are saved.
		user.onboarding_completed = True

		await self.db.commit()
		await self.db.refresh(preference)

		await self.invalidate_cache(str(user_id))
		return preference

	async def invalidate_cache(self, user_id: str) -> None:
		"""Hook for recommendation cache invalidation."""
		# TODO: Add actual redis key invalidation once key naming is finalized.
		_ = user_id

