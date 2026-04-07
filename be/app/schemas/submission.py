import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SubmissionStatus = Literal["pending", "approved", "rejected", "manual_review"]
AdminSubmissionFilterStatus = Literal["pending", "approved", "rejected", "manual_review"]


class SubmissionResponse(BaseModel):
	id: uuid.UUID
	user_quest_id: uuid.UUID
	image_url: str
	status: SubmissionStatus
	is_suspicious: bool
	rejection_reason: str | None
	created_at: datetime

	model_config = {"from_attributes": True}


class AdminSubmissionActionResponse(BaseModel):
	submission_id: uuid.UUID
	status: SubmissionStatus
	user_quest_status: Literal["submitted", "approved", "rejected"]
	xp_granted: int = 0


class RejectSubmissionRequest(BaseModel):
	reason: str = Field(min_length=3, max_length=500)


class AdminSubmissionItem(BaseModel):
	id: uuid.UUID
	user_quest_id: uuid.UUID
	quest_id: uuid.UUID
	user_id: uuid.UUID
	image_url: str
	status: SubmissionStatus
	is_suspicious: bool
	rejection_reason: str | None
	created_at: datetime


class AdminSubmissionListResponse(BaseModel):
	items: list[AdminSubmissionItem]
	total: int
	page: int
	page_size: int
