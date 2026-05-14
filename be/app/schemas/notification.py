import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse


NotificationType = Literal[
	"like",
	"comment",
	"follow",
	"quest_complete",
	"quest_rejected",
	"quest_suggest",
	"xp",
	"system",
]


class NotificationItem(BaseModel):
	id: uuid.UUID
	type: NotificationType | str
	data: dict | None = None
	is_read: bool
	created_at: datetime

	model_config = {"from_attributes": True}


class NotificationListResponse(PaginatedResponse[NotificationItem]):
	pass


class UnreadCountResponse(BaseModel):
	unread_count: int


class NotificationActionResponse(BaseModel):
	status: str = "ok"


class PushTokenRegisterRequest(BaseModel):
	token: str = Field(min_length=10, max_length=255)
	provider: Literal["expo", "fcm"] = "expo"
	platform: Literal["ios", "android", "web", "unknown"] = "unknown"


class PushTokenUnregisterRequest(BaseModel):
	token: str = Field(min_length=10, max_length=255)
