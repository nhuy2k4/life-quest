import asyncio
import logging
import uuid

import requests
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundException
from app.models.notification import Notification, UserPushToken
from app.schemas.common import PaginatedResponse
from app.schemas.notification import (
	NotificationActionResponse,
	NotificationItem,
	NotificationListResponse,
	PushTokenRegisterRequest,
	UnreadCountResponse,
)

logger = logging.getLogger(__name__)


class NotificationService:
	def __init__(self, db: AsyncSession) -> None:
		self.db = db

	async def list_notifications(
		self,
		*,
		user_id: uuid.UUID,
		page: int,
		page_size: int,
	) -> NotificationListResponse:
		offset = (page - 1) * page_size
		total = await self.db.scalar(
			select(func.count()).select_from(Notification).where(Notification.user_id == user_id)
		)
		rows = await self.db.scalars(
			select(Notification)
			.where(Notification.user_id == user_id)
			.order_by(Notification.created_at.desc())
			.offset(offset)
			.limit(page_size)
		)
		items = [NotificationItem.model_validate(row) for row in rows.all()]
		return NotificationListResponse.create(
			items=items,
			total=int(total or 0),
			page=page,
			page_size=page_size,
		)

	async def unread_count(self, *, user_id: uuid.UUID) -> UnreadCountResponse:
		total = await self.db.scalar(
			select(func.count())
			.select_from(Notification)
			.where(Notification.user_id == user_id, Notification.is_read.is_(False))
		)
		return UnreadCountResponse(unread_count=int(total or 0))

	async def mark_read(self, *, user_id: uuid.UUID, notification_id: uuid.UUID) -> NotificationActionResponse:
		notification = await self.db.scalar(
			select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
		)
		if notification is None:
			raise NotFoundException("Notification không tồn tại")
		notification.is_read = True
		await self.db.commit()
		return NotificationActionResponse()

	async def mark_all_read(self, *, user_id: uuid.UUID) -> NotificationActionResponse:
		await self.db.execute(
			update(Notification)
			.where(Notification.user_id == user_id, Notification.is_read.is_(False))
			.values(is_read=True)
		)
		await self.db.commit()
		return NotificationActionResponse()

	async def register_push_token(
		self,
		*,
		user_id: uuid.UUID,
		payload: PushTokenRegisterRequest,
	) -> NotificationActionResponse:
		existing = await self.db.scalar(select(UserPushToken).where(UserPushToken.token == payload.token))
		if existing is None:
			self.db.add(
				UserPushToken(
					user_id=user_id,
					token=payload.token,
					provider=payload.provider,
					platform=payload.platform,
					is_active=True,
				)
			)
		else:
			existing.user_id = user_id
			existing.provider = payload.provider
			existing.platform = payload.platform
			existing.is_active = True

		await self.db.commit()
		return NotificationActionResponse()

	async def unregister_push_token(self, *, user_id: uuid.UUID, token: str) -> NotificationActionResponse:
		existing = await self.db.scalar(
			select(UserPushToken).where(UserPushToken.user_id == user_id, UserPushToken.token == token)
		)
		if existing is not None:
			existing.is_active = False
			await self.db.commit()
		return NotificationActionResponse()

	async def create_notification(
		self,
		*,
		user_id: uuid.UUID,
		notification_type: str,
		data: dict | None = None,
		push_title: str | None = None,
		push_body: str | None = None,
		send_push: bool = True,
	) -> Notification:
		notification = Notification(
			user_id=user_id,
			type=notification_type,
			data=data or {},
			is_read=False,
		)
		self.db.add(notification)
		await self.db.flush()

		if send_push and settings.PUSH_NOTIFICATIONS_ENABLED:
			await self._send_push_to_user(
				user_id=user_id,
				title=push_title or self._default_title(notification_type),
				body=push_body or self._default_body(notification_type, data or {}),
				data={"notification_id": str(notification.id), "type": notification_type, **(data or {})},
			)

		return notification

	async def _send_push_to_user(
		self,
		*,
		user_id: uuid.UUID,
		title: str,
		body: str,
		data: dict,
	) -> None:
		rows = await self.db.scalars(
			select(UserPushToken).where(
				UserPushToken.user_id == user_id,
				UserPushToken.is_active.is_(True),
			)
		)
		push_tokens = rows.all()
		if not push_tokens:
			return

		messages = [
			{
				"to": item.token,
				"title": title,
				"body": body,
				"sound": "default",
				"data": data,
			}
			for item in push_tokens
			if item.provider == "expo"
		]

		if messages:
			try:
				await asyncio.to_thread(
					requests.post,
					settings.EXPO_PUSH_ENDPOINT,
					json=messages,
					timeout=5,
				)
			except Exception:
				logger.exception("Failed to send Expo push notification to user %s", user_id)

		fcm_tokens = [item.token for item in push_tokens if item.provider == "fcm"]
		if fcm_tokens and settings.FCM_PROJECT_ID and settings.FCM_SERVICE_ACCOUNT_FILE:
			await self._send_fcm_v1(tokens=fcm_tokens, title=title, body=body, data=data)

	async def _send_fcm_v1(self, *, tokens: list[str], title: str, body: str, data: dict) -> None:
		try:
			credentials = service_account.Credentials.from_service_account_file(
				settings.FCM_SERVICE_ACCOUNT_FILE,
				scopes=["https://www.googleapis.com/auth/firebase.messaging"],
			)
			credentials.refresh(GoogleAuthRequest())
			url = f"https://fcm.googleapis.com/v1/projects/{settings.FCM_PROJECT_ID}/messages:send"
			headers = {
				"Authorization": f"Bearer {credentials.token}",
				"Content-Type": "application/json",
			}
			string_data = {key: str(value) for key, value in data.items() if value is not None}

			for token in tokens:
				payload = {
					"message": {
						"token": token,
						"notification": {"title": title, "body": body},
						"data": string_data,
					}
				}
				await asyncio.to_thread(requests.post, url, headers=headers, json=payload, timeout=5)
		except Exception:
			logger.exception("Failed to send FCM v1 push notification")

	@staticmethod
	def _default_title(notification_type: str) -> str:
		if notification_type == "like":
			return "New like"
		if notification_type == "comment":
			return "New comment"
		if notification_type == "follow":
			return "New follower"
		if notification_type == "chat_message":
			return "New message"
		if notification_type == "quest_complete":
			return "Quest approved"
		if notification_type == "quest_rejected":
			return "Quest needs another photo"
		return "LifeQuest"

	@staticmethod
	def _default_body(notification_type: str, data: dict) -> str:
		actor = data.get("actor_username")
		if notification_type == "like":
			return f"{actor or 'Someone'} liked your post."
		if notification_type == "comment":
			return f"{actor or 'Someone'} commented on your post."
		if notification_type == "follow":
			return f"{actor or 'Someone'} followed you."
		if notification_type == "chat_message":
			return f"{data.get('sender_username') or 'Someone'} sent you a message."
		if notification_type == "quest_complete":
			return "Your quest was approved and XP was added."
		if notification_type == "quest_rejected":
			return "Your quest photo was rejected. You can update it and try again."
		return "You have a new notification."
