import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.audit import AuditLog
from app.models.enums import XpSource
from app.models.quest import Quest
from app.models.social import Comment, Post
from app.models.user import User
from app.models.xp_transaction import XpTransaction
from app.schemas.admin import (
	AdminQuestItem,
	AdminQuestListResponse,
	AdminQuestUpdateRequest,
	AdminUserItem,
	AdminUserListResponse,
	AdminUserXpAdjustRequest,
	AdminUserXpAdjustResponse,
)


class AdminService:
	def __init__(self, db: AsyncSession) -> None:
		self.db = db

	async def list_users(self, *, page: int, page_size: int) -> AdminUserListResponse:
		offset = (page - 1) * page_size
		total = await self.db.scalar(select(func.count()).select_from(User))
		rows = await self.db.scalars(
			select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
		)
		items = [AdminUserItem.model_validate(user) for user in rows.all()]
		return AdminUserListResponse.create(items=items, total=int(total or 0), page=page, page_size=page_size)

	async def set_user_ban(self, *, user_id: uuid.UUID, is_banned: bool) -> None:
		user = await self.db.scalar(select(User).where(User.id == user_id))
		if user is None:
			raise NotFoundException("User không tồn tại")
		user.is_banned = is_banned
		self.db.add(AuditLog(action="user_ban", target_type="user", target_id=user.id))
		await self.db.commit()

	async def adjust_user_xp(
		self,
		*,
		user_id: uuid.UUID,
		payload: AdminUserXpAdjustRequest,
	) -> AdminUserXpAdjustResponse:
		user = await self.db.scalar(select(User).where(User.id == user_id))
		if user is None:
			raise NotFoundException("User không tồn tại")
		if payload.amount == 0:
			raise BadRequestException("Số XP điều chỉnh phải khác 0")

		transaction = XpTransaction(
			user_id=user.id,
			submission_id=None,
			amount=payload.amount,
			source=XpSource.ADMIN_ADJUST,
		)
		self.db.add(transaction)
		user.xp = max(user.xp + payload.amount, 0)
		self.db.add(AuditLog(
			action="xp_adjust",
			target_type="user",
			target_id=user.id,
			meta={"amount": payload.amount, "reason": payload.reason},
		))
		await self.db.commit()
		return AdminUserXpAdjustResponse(user_id=user.id, amount=payload.amount, new_xp=user.xp)

	async def list_quests(self, *, page: int, page_size: int) -> AdminQuestListResponse:
		offset = (page - 1) * page_size
		total = await self.db.scalar(select(func.count()).select_from(Quest))
		rows = await self.db.scalars(
			select(Quest).order_by(Quest.created_at.desc()).offset(offset).limit(page_size)
		)
		items = [
			AdminQuestItem(
				id=quest.id,
				title=quest.title,
				difficulty=quest.difficulty.value,
				xp_reward=quest.xp_reward,
				is_active=quest.is_active,
				created_at=quest.created_at,
			)
			for quest in rows.all()
		]
		return AdminQuestListResponse.create(items=items, total=int(total or 0), page=page, page_size=page_size)

	async def update_quest(self, *, quest_id: uuid.UUID, payload: AdminQuestUpdateRequest) -> None:
		quest = await self.db.scalar(select(Quest).where(Quest.id == quest_id))
		if quest is None:
			raise NotFoundException("Quest không tồn tại")

		if payload.is_active is not None:
			quest.is_active = payload.is_active
		if payload.xp_reward is not None:
			quest.xp_reward = payload.xp_reward

		self.db.add(AuditLog(action="quest_update", target_type="quest", target_id=quest.id))
		await self.db.commit()

	async def delete_post(self, *, post_id: uuid.UUID) -> None:
		post = await self.db.scalar(
			select(Post).options(selectinload(Post.comments)).where(Post.id == post_id)
		)
		if post is None:
			raise NotFoundException("Post không tồn tại")

		await self.db.delete(post)
		self.db.add(AuditLog(action="post_delete", target_type="post", target_id=post.id))
		await self.db.commit()

	async def delete_comment(self, *, comment_id: uuid.UUID) -> None:
		comment = await self.db.scalar(select(Comment).where(Comment.id == comment_id))
		if comment is None:
			raise NotFoundException("Comment không tồn tại")

		await self.db.delete(comment)
		self.db.add(AuditLog(action="comment_delete", target_type="comment", target_id=comment.id))
		await self.db.commit()
