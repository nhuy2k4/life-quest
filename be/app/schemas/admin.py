import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse


class AdminUserItem(BaseModel):
	id: uuid.UUID
	username: str
	email: str
	role: str
	is_banned: bool
	created_at: datetime

	model_config = {"from_attributes": True}


class AdminUserListResponse(PaginatedResponse[AdminUserItem]):
	pass


class AdminUserBanRequest(BaseModel):
	is_banned: bool


class AdminUserXpAdjustRequest(BaseModel):
	amount: int = Field(ge=-100000, le=100000)
	reason: str | None = Field(default=None, max_length=200)


class AdminUserXpAdjustResponse(BaseModel):
	user_id: uuid.UUID
	amount: int
	new_xp: int


class AdminQuestItem(BaseModel):
	id: uuid.UUID
	title: str
	difficulty: str
	xp_reward: int
	is_active: bool
	created_at: datetime

	model_config = {"from_attributes": True}


class AdminQuestListResponse(PaginatedResponse[AdminQuestItem]):
	pass


class AdminQuestUpdateRequest(BaseModel):
	is_active: bool | None = None
	xp_reward: int | None = Field(default=None, ge=0)


class AdminPostActionResponse(BaseModel):
	status: str = "ok"


class AdminCommentActionResponse(BaseModel):
	status: str = "ok"
