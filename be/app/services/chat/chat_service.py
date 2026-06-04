import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.chat import Conversation, Message
from app.models.social import Follow
from app.models.user import User
from app.schemas.chat import (
	ConversationResponse,
	MessageCreateRequest,
	MessageResponse,
)
from app.schemas.user import UserPublicResponse
from app.services.notification.notification_service import NotificationService


class ChatService:
	def __init__(self, db: AsyncSession) -> None:
		self.db = db

	async def list_conversations(
		self,
		*,
		user_id: uuid.UUID,
		page: int,
		page_size: int,
	) -> tuple[list[ConversationResponse], int]:
		offset = (page - 1) * page_size
		member_filter = self._conversation_member_filter(user_id)
		total = await self.db.scalar(select(func.count()).select_from(Conversation).where(member_filter))
		rows = await self.db.scalars(
			select(Conversation)
			.options(
				selectinload(Conversation.user_one),
				selectinload(Conversation.user_two),
				selectinload(Conversation.last_message).selectinload(Message.sender),
			)
			.where(member_filter)
			.order_by(Conversation.last_message_at.desc().nullslast(), Conversation.updated_at.desc())
			.offset(offset)
			.limit(page_size)
		)
		conversations = rows.all()
		items = [await self._to_conversation_response(item, user_id=user_id) for item in conversations]
		return items, int(total or 0)

	async def get_or_create_conversation(
		self,
		*,
		user_id: uuid.UUID,
		target_user_id: uuid.UUID,
	) -> ConversationResponse:
		conversation = await self._get_or_create_conversation_model(
			user_id=user_id,
			target_user_id=target_user_id,
		)
		await self.db.commit()
		stored = await self._get_conversation(conversation_id=conversation.id)
		if stored is None:
			raise NotFoundException("Conversation khong ton tai")
		return await self._to_conversation_response(stored, user_id=user_id)

	async def list_messages(
		self,
		*,
		user_id: uuid.UUID,
		conversation_id: uuid.UUID,
		page: int,
		page_size: int,
	) -> tuple[list[MessageResponse], int]:
		await self._get_conversation_for_user(conversation_id=conversation_id, user_id=user_id)
		offset = (page - 1) * page_size
		total = await self.db.scalar(
			select(func.count()).select_from(Message).where(Message.conversation_id == conversation_id)
		)
		rows = await self.db.scalars(
			select(Message)
			.options(selectinload(Message.sender))
			.where(Message.conversation_id == conversation_id)
			.order_by(Message.created_at.desc(), Message.id.desc())
			.offset(offset)
			.limit(page_size)
		)
		messages = list(reversed(rows.all()))
		return [self._to_message_response(item, current_user_id=user_id) for item in messages], int(total or 0)

	async def send_message(
		self,
		*,
		user_id: uuid.UUID,
		conversation_id: uuid.UUID | None,
		target_user_id: uuid.UUID | None,
		payload: MessageCreateRequest,
		send_push: bool = True,
	) -> tuple[MessageResponse, uuid.UUID]:
		if conversation_id is None and target_user_id is None:
			raise BadRequestException("Can conversation_id hoac target_user_id")

		if conversation_id is not None:
			conversation = await self._get_conversation_for_user(conversation_id=conversation_id, user_id=user_id)
		else:
			conversation = await self._get_or_create_conversation_model(
				user_id=user_id,
				target_user_id=target_user_id,
			)

		recipient_id = self._other_user_id(conversation, user_id)
		message = Message(
			conversation_id=conversation.id,
			sender_id=user_id,
			content=payload.content.strip(),
			message_type="text",
		)
		self.db.add(message)
		await self.db.flush()

		conversation.last_message_id = message.id
		conversation.last_message_at = message.created_at or datetime.now(timezone.utc)

		if send_push:
			sender = await self.db.scalar(select(User).where(User.id == user_id))
			await NotificationService(self.db).create_notification(
				user_id=recipient_id,
				notification_type="chat_message",
				data={
					"conversation_id": str(conversation.id),
					"message_id": str(message.id),
					"sender_id": str(user_id),
					"sender_username": sender.username if sender else None,
				},
				push_title=sender.username if sender else "New message",
				push_body=payload.content.strip()[:120],
			)

		await self.db.commit()
		stored = await self.db.scalar(
			select(Message)
			.options(selectinload(Message.sender))
			.where(Message.id == message.id)
		)
		if stored is None:
			raise NotFoundException("Message khong ton tai")
		return self._to_message_response(stored, current_user_id=user_id), recipient_id

	async def mark_read(self, *, user_id: uuid.UUID, conversation_id: uuid.UUID) -> tuple[int, uuid.UUID]:
		conversation = await self._get_conversation_for_user(conversation_id=conversation_id, user_id=user_id)
		result = await self.db.execute(
			update(Message)
			.where(
				Message.conversation_id == conversation_id,
				Message.sender_id != user_id,
				Message.read_at.is_(None),
			)
			.values(read_at=datetime.now(timezone.utc))
		)
		await self.db.commit()
		return int(result.rowcount or 0), self._other_user_id(conversation, user_id)

	async def _get_or_create_conversation_model(
		self,
		*,
		user_id: uuid.UUID,
		target_user_id: uuid.UUID | None,
	) -> Conversation:
		if target_user_id is None:
			raise BadRequestException("target_user_id khong hop le")
		if target_user_id == user_id:
			raise BadRequestException("Khong the chat voi chinh minh")

		target = await self.db.scalar(select(User).where(User.id == target_user_id))
		if target is None:
			raise NotFoundException("User khong ton tai")

		if not await self._can_chat(user_id=user_id, target_user_id=target_user_id):
			raise ForbiddenException("Can follow mot chieu de bat dau chat")

		user_one_id, user_two_id = self._normalize_pair(user_id, target_user_id)
		conversation = await self.db.scalar(
			select(Conversation).where(
				Conversation.user_one_id == user_one_id,
				Conversation.user_two_id == user_two_id,
			)
		)
		if conversation is not None:
			return conversation

		conversation = Conversation(user_one_id=user_one_id, user_two_id=user_two_id)
		self.db.add(conversation)
		await self.db.flush()
		return conversation

	async def _get_conversation(self, *, conversation_id: uuid.UUID) -> Conversation | None:
		return await self.db.scalar(
			select(Conversation)
			.options(
				selectinload(Conversation.user_one),
				selectinload(Conversation.user_two),
				selectinload(Conversation.last_message).selectinload(Message.sender),
			)
			.where(Conversation.id == conversation_id)
		)

	async def _get_conversation_for_user(self, *, conversation_id: uuid.UUID, user_id: uuid.UUID) -> Conversation:
		conversation = await self._get_conversation(conversation_id=conversation_id)
		if conversation is None:
			raise NotFoundException("Conversation khong ton tai")
		if conversation.user_one_id != user_id and conversation.user_two_id != user_id:
			raise ForbiddenException("Ban khong thuoc conversation nay")
		return conversation

	async def _can_chat(self, *, user_id: uuid.UUID, target_user_id: uuid.UUID) -> bool:
		follow = await self.db.scalar(
			select(Follow).where(
				or_(
					and_(Follow.follower_id == user_id, Follow.following_id == target_user_id),
					and_(Follow.follower_id == target_user_id, Follow.following_id == user_id),
				)
			)
		)
		return follow is not None

	async def _is_friend(self, *, user_id: uuid.UUID, target_user_id: uuid.UUID) -> bool:
		count = await self.db.scalar(
			select(func.count())
			.select_from(Follow)
			.where(
				or_(
					and_(Follow.follower_id == user_id, Follow.following_id == target_user_id),
					and_(Follow.follower_id == target_user_id, Follow.following_id == user_id),
				)
			)
		)
		return int(count or 0) >= 2

	async def _unread_count(self, *, conversation_id: uuid.UUID, user_id: uuid.UUID) -> int:
		count = await self.db.scalar(
			select(func.count())
			.select_from(Message)
			.where(
				Message.conversation_id == conversation_id,
				Message.sender_id != user_id,
				Message.read_at.is_(None),
			)
		)
		return int(count or 0)

	async def _to_conversation_response(self, conversation: Conversation, *, user_id: uuid.UUID) -> ConversationResponse:
		other_user = conversation.user_two if conversation.user_one_id == user_id else conversation.user_one
		return ConversationResponse(
			id=conversation.id,
			other_user=UserPublicResponse.model_validate(other_user),
			is_friend=await self._is_friend(user_id=user_id, target_user_id=other_user.id),
			last_message=(
				self._to_message_response(conversation.last_message, current_user_id=user_id)
				if conversation.last_message
				else None
			),
			unread_count=await self._unread_count(conversation_id=conversation.id, user_id=user_id),
			created_at=conversation.created_at,
			updated_at=conversation.updated_at,
			last_message_at=conversation.last_message_at,
		)

	@staticmethod
	def _to_message_response(message: Message, *, current_user_id: uuid.UUID) -> MessageResponse:
		return MessageResponse(
			id=message.id,
			conversation_id=message.conversation_id,
			sender=UserPublicResponse.model_validate(message.sender),
			content=message.content,
			message_type=message.message_type,
			read_at=message.read_at,
			created_at=message.created_at,
			is_mine=message.sender_id == current_user_id,
		)

	@staticmethod
	def _conversation_member_filter(user_id: uuid.UUID):
		return or_(Conversation.user_one_id == user_id, Conversation.user_two_id == user_id)

	@staticmethod
	def _normalize_pair(user_id: uuid.UUID, target_user_id: uuid.UUID) -> tuple[uuid.UUID, uuid.UUID]:
		return (user_id, target_user_id) if str(user_id) < str(target_user_id) else (target_user_id, user_id)

	@staticmethod
	def _other_user_id(conversation: Conversation, user_id: uuid.UUID) -> uuid.UUID:
		return conversation.user_two_id if conversation.user_one_id == user_id else conversation.user_one_id
