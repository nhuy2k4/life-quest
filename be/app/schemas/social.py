import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse
from app.schemas.user import UserPublicResponse


class PostQuestInfo(BaseModel):
	id: uuid.UUID
	title: str
	description: str | None = None
	xp_reward: int

	model_config = {"from_attributes": True}


class PostCreateRequest(BaseModel):
	submission_id: uuid.UUID | None = None
	quest_id: uuid.UUID | None = None
	image_url: str | None = None
	caption: str | None = None



class PostResponse(BaseModel):
	id: uuid.UUID
	submission_id: uuid.UUID | None
	submission_image_url: str | None = None
	caption: str | None = None
	quest: PostQuestInfo | None = None
	user: UserPublicResponse
	like_count: int
	comment_count: int
	liked_by_me: bool = False
	created_at: datetime

	model_config = {"from_attributes": True}


class CommentCreateRequest(BaseModel):
	content: str = Field(min_length=1, max_length=2000)
	parent_id: uuid.UUID | None = None


class CommentResponse(BaseModel):
	id: uuid.UUID
	post_id: uuid.UUID
	parent_id: uuid.UUID | None
	user: UserPublicResponse
	content: str
	is_deleted: bool
	created_at: datetime

	model_config = {"from_attributes": True}


class FeedResponse(PaginatedResponse[PostResponse]):
	pass


class CommentListResponse(PaginatedResponse[CommentResponse]):
	pass


class FollowListResponse(PaginatedResponse[UserPublicResponse]):
	pass


class FollowResponse(BaseModel):
	status: str = "ok"


class LikeResponse(BaseModel):
	status: str = "ok"
