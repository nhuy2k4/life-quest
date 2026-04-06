import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.user import User
from app.schemas.user import UpdateProfileRequest


class UserService:
	"""Business logic for user profile operations."""

	def __init__(self, db: AsyncSession):
		self.db = db

	async def get_me(self, user_id: uuid.UUID) -> User:
		user = await self.db.scalar(select(User).where(User.id == user_id))
		if user is None:
			raise NotFoundException("User không tồn tại")
		return user

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

