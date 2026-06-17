import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse
from app.schemas.social import PostResponse
from app.schemas.user import UserPublicResponse


EventStatus = Literal["draft", "active", "ended"]


class EventRewardTier(BaseModel):
	rank_from: int = Field(ge=1)
	rank_to: int = Field(ge=1)
	bonus_xp: int = Field(ge=0, default=0)
	badge_id: uuid.UUID | None = None


class EventQuestItem(BaseModel):
	id: uuid.UUID
	title: str
	description: str | None = None
	xp_reward: int

	model_config = {"from_attributes": True}


class EventCreateRequest(BaseModel):
	title: str = Field(min_length=1, max_length=255)
	description: str | None = None
	banner_url: str | None = None
	start_at: datetime
	end_at: datetime
	status: EventStatus | None = None
	reward_config: list[EventRewardTier] = Field(default_factory=list)
	quest_ids: list[uuid.UUID] = Field(default_factory=list)
	location_name: str | None = None
	latitude: float | None = None
	longitude: float | None = None
	radius_m: float | None = None



class EventUpdateRequest(BaseModel):
	title: str | None = Field(default=None, min_length=1, max_length=255)
	description: str | None = None
	banner_url: str | None = None
	start_at: datetime | None = None
	end_at: datetime | None = None
	status: EventStatus | None = None
	reward_config: list[EventRewardTier] | None = None
	quest_ids: list[uuid.UUID] | None = None
	location_name: str | None = None
	latitude: float | None = None
	longitude: float | None = None
	radius_m: float | None = None



class EventListItem(BaseModel):
	id: uuid.UUID
	title: str
	description: str | None = None
	banner_url: str | None = None
	start_at: datetime
	end_at: datetime
	status: EventStatus
	location_name: str | None = None
	latitude: float | None = None
	longitude: float | None = None
	radius_m: float | None = None


	model_config = {"from_attributes": True}


class EventDetailResponse(BaseModel):
	id: uuid.UUID
	title: str
	description: str | None = None
	banner_url: str | None = None
	start_at: datetime
	end_at: datetime
	status: EventStatus
	reward_config: list[EventRewardTier]
	quests: list[EventQuestItem]
	is_joined: bool = False
	location_name: str | None = None
	latitude: float | None = None
	longitude: float | None = None
	radius_m: float | None = None


	model_config = {"from_attributes": True}


class EventLeaderboardPost(BaseModel):
	id: uuid.UUID | None = None
	image_url: str | None = None
	like_count: int = 0
	is_deleted: bool = False


class EventLeaderboardItem(BaseModel):
	rank: int
	user: UserPublicResponse
	post: EventLeaderboardPost


class EventLeaderboardResponse(BaseModel):
	items: list[EventLeaderboardItem]
	total: int


class EventActionResponse(BaseModel):
	status: str = "ok"


class EventPostListResponse(PaginatedResponse[PostResponse]):
	pass
