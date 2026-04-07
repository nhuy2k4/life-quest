import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


QuestDifficulty = Literal["easy", "medium", "hard"]
QuestUserStatus = Literal["not_started", "started", "submitted", "approved", "rejected"]


class QuestListItemResponse(BaseModel):
	id: uuid.UUID
	title: str
	description: str | None = None
	xp_reward: int
	difficulty: QuestDifficulty
	time_limit_hours: int | None = None
	location_required: bool
	is_active: bool
	user_status: QuestUserStatus = "not_started"

	model_config = {"from_attributes": True}


class QuestDetailResponse(BaseModel):
	id: uuid.UUID
	title: str
	description: str | None = None
	xp_reward: int
	difficulty: QuestDifficulty
	approval_rate: float
	time_limit_hours: int | None = None
	location_required: bool
	is_active: bool
	user_status: QuestUserStatus = "not_started"
	started_at: datetime | None = None
	expires_at: datetime | None = None

	model_config = {"from_attributes": True}


class StartQuestResponse(BaseModel):
	user_quest_id: uuid.UUID
	quest_id: uuid.UUID
	status: QuestUserStatus
	started_at: datetime | None
	expires_at: datetime | None


class SubmitQuestRequest(BaseModel):
	image_url: str = Field(min_length=3, max_length=500)
	cloudinary_public_id: str = Field(min_length=1, max_length=255)
	file_hash: str = Field(min_length=32, max_length=64)


class SubmitQuestResponse(BaseModel):
	submission_id: uuid.UUID
	user_quest_id: uuid.UUID
	status: QuestUserStatus
	submission_status: Literal["pending", "approved", "rejected", "manual_review"]
	submitted_at: datetime
