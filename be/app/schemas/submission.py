import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SubmissionResponse(BaseModel):
	id: uuid.UUID
	user_quest_id: uuid.UUID
	image_url: str
	status: Literal["pending", "approved", "rejected", "manual_review"]
	is_suspicious: bool
	rejection_reason: str | None
	created_at: datetime

	model_config = {"from_attributes": True}
