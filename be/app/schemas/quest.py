import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


QuestUserStatus = Literal["not_started", "started", "submitted", "approved", "rejected"]


class QuestListItemResponse(BaseModel):
	id: uuid.UUID
	poi_id: uuid.UUID | None = None
	poi_name: str | None = None
	image_url: str | None = None
	rendered_text: str
	labels: list[str]
	min_confidence: float
	xp_reward: int
	is_active: bool
	user_status: QuestUserStatus = "not_started"

	model_config = {"from_attributes": True}


class QuestDetailResponse(BaseModel):
	id: uuid.UUID
	poi_id: uuid.UUID | None = None
	poi_name: str | None = None
	image_url: str | None = None

	rendered_text: str
	description: str | None = None
	labels: list[str]
	min_confidence: float

	xp_reward: int
	base_xp: int
	poi_bonus_xp: int
	total_xp_with_poi: int

	poi_required: bool = False
	is_active: bool
	is_event: bool = False

	user_status: QuestUserStatus = "not_started"
	started_at: datetime | None = None

	event_id: uuid.UUID | None = None
	event_location_name: str | None = None
	event_latitude: float | None = None
	event_longitude: float | None = None
	event_radius_m: float | None = None

	model_config = {"from_attributes": True}


class StartQuestResponse(BaseModel):
	user_quest_id: uuid.UUID
	quest_id: uuid.UUID
	poi_id: uuid.UUID | None = None
	status: QuestUserStatus
	started_at: datetime | None


class SubmitQuestRequest(BaseModel):
	post_id: uuid.UUID | None = None
	poi_id: uuid.UUID | None = None
	image_url: str = Field(min_length=3, max_length=500)
	cloudinary_public_id: str = Field(min_length=1, max_length=255)
	file_hash: str = Field(min_length=32, max_length=64)
	lat: float | None = None
	lng: float | None = None
	location_accuracy_m: float | None = None
	is_event: bool = False


class SubmitQuestResponse(BaseModel):
	submission_id: uuid.UUID
	post_id: uuid.UUID | None = None
	user_quest_id: uuid.UUID
	poi_id: uuid.UUID | None = None
	status: QuestUserStatus
	submission_status: Literal["pending", "processing", "approved", "rejected", "manual_review"]
	submitted_at: datetime
	retry_count: int = 0
	max_retry_count: int = 3


class RecommendQuestFromImageRequest(BaseModel):
	image_url: str = Field(min_length=1, max_length=1000)
	lat: float | None = None
	lng: float | None = None
