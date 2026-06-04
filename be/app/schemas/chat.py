import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse
from app.schemas.user import UserPublicResponse


class ConversationCreateRequest(BaseModel):
	target_user_id: uuid.UUID


class MessageCreateRequest(BaseModel):
	content: str = Field(min_length=1, max_length=4000)


class MessageResponse(BaseModel):
	id: uuid.UUID
	conversation_id: uuid.UUID
	sender: UserPublicResponse
	content: str
	message_type: str = "text"
	read_at: datetime | None = None
	created_at: datetime
	is_mine: bool = False


class ConversationResponse(BaseModel):
	id: uuid.UUID
	other_user: UserPublicResponse
	is_friend: bool = False
	last_message: MessageResponse | None = None
	unread_count: int = 0
	created_at: datetime
	updated_at: datetime
	last_message_at: datetime | None = None


class ConversationListResponse(PaginatedResponse[ConversationResponse]):
	pass


class MessageListResponse(PaginatedResponse[MessageResponse]):
	pass


class ChatActionResponse(BaseModel):
	status: str = "ok"
