import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.enums import UserQuestStatus
from app.models.social import Follow, Post
from app.models.user import User
from app.models.user_quest import UserQuest
from app.schemas.user import UpdateProfileRequest, UserProfileStatsResponse, UserPublicProfileResponse


class UserService:
	"""Business logic for user profile operations."""

	def __init__(self, db: AsyncSession):
		self.db = db

	async def _update_streak_if_needed(self, user: User) -> None:
		from datetime import datetime, timezone, timedelta
		from app.models.submission import Submission
		from app.models.user_quest import UserQuest
		from app.models.enums import SubmissionStatus

		stmt = (
			select(Submission.created_at)
			.join(UserQuest, Submission.user_quest_id == UserQuest.id)
			.where(
				UserQuest.user_id == user.id,
				Submission.status == SubmissionStatus.APPROVED
			)
			.order_by(Submission.created_at.desc())
			.limit(1)
		)
		last_approved_time = await self.db.scalar(stmt)
		
		if last_approved_time:
			if last_approved_time.tzinfo is None:
				last_approved_time = last_approved_time.replace(tzinfo=timezone.utc)
			
			now = datetime.now(timezone.utc)
			vn_tz = timezone(timedelta(hours=7))
			
			last_approved_date = last_approved_time.astimezone(vn_tz).date()
			current_date = now.astimezone(vn_tz).date()
			
			if current_date > last_approved_date + timedelta(days=1):
				if user.streak_days > 0:
					user.streak_days = 0
					await self.db.commit()
			elif user.streak_days == 0:
				user.streak_days = 1
				await self.db.commit()
		else:
			if user.streak_days > 0:
				user.streak_days = 0
				await self.db.commit()

	async def get_me(self, user_id: uuid.UUID) -> User:
		user = await self.db.scalar(select(User).where(User.id == user_id))
		if user is None:
			raise NotFoundException("User không tồn tại")
		await self._update_streak_if_needed(user)
		return user

	async def get_public_profile(self, *, viewer_id: uuid.UUID, target_user_id: uuid.UUID) -> UserPublicProfileResponse:
		user = await self.db.scalar(select(User).where(User.id == target_user_id))
		if user is None:
			raise NotFoundException("User không tồn tại")
		await self._update_streak_if_needed(user)

		posts_count = await self.db.scalar(select(func.count()).select_from(Post).where(Post.user_id == target_user_id))
		followers_count = await self.db.scalar(
			select(func.count()).select_from(Follow).where(Follow.following_id == target_user_id)
		)
		following_count = await self.db.scalar(
			select(func.count()).select_from(Follow).where(Follow.follower_id == target_user_id)
		)
		quests_completed = await self.db.scalar(
			select(func.count())
			.select_from(UserQuest)
			.where(UserQuest.user_id == target_user_id, UserQuest.status == UserQuestStatus.APPROVED)
		)
		is_following = False
		if viewer_id != target_user_id:
			is_following = (
				await self.db.scalar(
					select(Follow).where(
						Follow.follower_id == viewer_id,
						Follow.following_id == target_user_id,
					)
				)
			) is not None

		return UserPublicProfileResponse(
			id=user.id,
			username=user.username,
			display_name=user.display_name,
			bio=user.bio,
			avatar_url=user.avatar_url,
			level_id=user.level_id,
			xp=user.xp,
			streak_days=user.streak_days,
			is_following=is_following,
			is_self=viewer_id == target_user_id,
			stats=UserProfileStatsResponse(
				posts=int(posts_count or 0),
				streak=user.streak_days,
				quests_completed=int(quests_completed or 0),
				followers=int(followers_count or 0),
				following=int(following_count or 0),
			),
		)

	async def update_me(self, user_id: uuid.UUID, payload: UpdateProfileRequest) -> User:
		user = await self.get_me(user_id)

		updates = payload.model_dump(exclude_unset=True)
		if not updates:
			raise BadRequestException("Không có trường hợp lệ để cập nhật")

		username = updates.get("username")
		email = updates.get("email")
		if username is not None:
			username = username.strip()
			if not username:
				raise BadRequestException("username không được để trống")
			updates["username"] = username

		if email is not None:
			updates["email"] = str(email).strip().lower()

		display_name = updates.get("display_name")
		if display_name is not None:
			display_name = display_name.strip()
			updates["display_name"] = display_name or None

		bio = updates.get("bio")
		if bio is not None:
			bio = bio.strip()
			if len(bio) > 150:
				raise BadRequestException("bio khÃ´ng Ä‘Æ°á»£c vÆ°á»£t quÃ¡ 150 kÃ½ tá»±")
			updates["bio"] = bio or None

		duplicate_stmt = select(User).where(
			User.id != user_id,
			or_(
				User.username == updates.get("username", user.username),
				User.email == updates.get("email", user.email),
			),
		)
		duplicate = await self.db.scalar(duplicate_stmt)
		if duplicate is not None:
			raise BadRequestException("username hoặc email đã tồn tại")

		for field, value in updates.items():
			setattr(user, field, value)

		await self.db.commit()
		await self.db.refresh(user)
		return user

