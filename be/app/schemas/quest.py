import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


QuestUserStatus = Literal["not_started", "started", "submitted", "approved", "rejected"]


class QuestListItemResponse(BaseModel):
	id: uuid.UUID
	rendered_text: str
	labels: list[str]
	min_confidence: float
	poi_required: bool
	xp_reward: int
	is_active: bool
	user_status: QuestUserStatus = "not_started"

	model_config = {"from_attributes": True}


class QuestDetailResponse(BaseModel):
	id: uuid.UUID
	rendered_text: str
	labels: list[str]
	min_confidence: float
	poi_required: bool
	poi_id: uuid.UUID | None = None
	xp_reward: int
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
	lat: float | None = None
	lng: float | None = None
	location_accuracy_m: float | None = None
	location_captured_at: datetime | None = None


class SubmitQuestResponse(BaseModel):
	submission_id: uuid.UUID
	user_quest_id: uuid.UUID
	status: QuestUserStatus
	submission_status: Literal["pending", "processing", "approved", "rejected", "manual_review"]
	submitted_at: datetime
	retry_count: int = 0
	max_retry_count: int = 3


class RecommendQuestFromImageRequest(BaseModel):
	image_url: str = Field(min_length=1, max_length=1000)
	lat: float | None = None
	lng: float | None = None


