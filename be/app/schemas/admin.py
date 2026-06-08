import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse
from app.schemas.user import UserPublicResponse

from app.schemas.common import PaginatedResponse


class AdminUserItem(BaseModel):
	id: uuid.UUID
	username: str
	display_name: Optional[str] = None
	avatar_url: Optional[str] = None
	email: str
	role: str
	is_banned: bool
	is_verified: bool
	level_id: int
	xp: int
	streak_days: int
	trust_score: float
	created_at: datetime

	model_config = {"from_attributes": True}


class AdminUserListResponse(PaginatedResponse[AdminUserItem]):
	pass


class AdminUserBanRequest(BaseModel):
	is_banned: bool


class AdminUserUpdateRequest(BaseModel):
	username: Optional[str] = Field(default=None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
	email: Optional[str] = Field(default=None, max_length=255)
	password: Optional[str] = Field(default=None, min_length=6, max_length=128)


class AdminUserXpAdjustRequest(BaseModel):
	amount: int = Field(ge=-100000, le=100000)
	reason: str | None = Field(default=None, max_length=200)


class AdminUserXpAdjustResponse(BaseModel):
	user_id: uuid.UUID
	amount: int
	new_xp: int


class AdminCategoryItem(BaseModel):
	id: int
	name: str
	slug: Optional[str] = None

	model_config = {"from_attributes": True}


class AdminQuestItem(BaseModel):
	id: uuid.UUID
	title: str
	description: Optional[str] = None
	difficulty: str
	xp_reward: int
	approval_rate: float = 0.0
	time_limit_hours: Optional[int] = None
	categories: list[AdminCategoryItem] = []
	is_active: bool
	created_at: datetime

	model_config = {"from_attributes": True}


class AdminQuestListResponse(PaginatedResponse[AdminQuestItem]):
	pass


class AdminQuestUpdateRequest(BaseModel):
	title: Optional[str] = Field(default=None, min_length=1, max_length=255)
	description: Optional[str] = None
	difficulty: Optional[str] = Field(default=None, pattern="^(easy|medium|hard)$")
	is_active: bool | None = None
	xp_reward: int | None = Field(default=None, ge=0)
	time_limit_hours: Optional[int] = Field(default=None, ge=1)


class AdminQuestCompletionStat(BaseModel):
	quest_id: uuid.UUID
	title: str
	completed_count: int


class AdminPostInteractionStat(BaseModel):
	post_id: uuid.UUID
	caption: Optional[str] = None
	author: str
	like_count: int
	comment_count: int
	interaction_count: int
	created_at: datetime


class AdminEventParticipationStat(BaseModel):
	event_id: uuid.UUID
	title: str
	status: str
	participant_count: int
	start_at: datetime
	end_at: datetime


class AdminDashboardStatsResponse(BaseModel):
	quests_completed_today: list[AdminQuestCompletionStat]
	quests_completed_this_month: list[AdminQuestCompletionStat]
	top_interaction_posts: list[AdminPostInteractionStat]
	top_participation_events: list[AdminEventParticipationStat]


class AdminPostActionResponse(BaseModel):
	status: str = "ok"


class AdminCommentActionResponse(BaseModel):
	status: str = "ok"


class AdminPostItem(BaseModel):
	id: uuid.UUID
	user: UserPublicResponse
	caption: Optional[str] = None
	media_url: Optional[str] = None
	location_name: Optional[str] = None
	quest_id: Optional[uuid.UUID] = None
	quest_title: Optional[str] = None
	submission_id: Optional[uuid.UUID] = None
	like_count: int
	comment_count: int
	created_at: datetime


class AdminPostListResponse(PaginatedResponse[AdminPostItem]):
	pass


class AdminCommentItem(BaseModel):
	id: uuid.UUID
	post_id: uuid.UUID
	user: UserPublicResponse
	content: str
	is_deleted: bool
	created_at: datetime


class AdminCommentListResponse(PaginatedResponse[AdminCommentItem]):
	pass


BADGE_RARITIES = {"common", "rare", "epic", "legendary"}
BADGE_CATEGORIES = {"quests", "social", "streak", "progression", "trust", "general"}
BADGE_CONDITION_TYPES = {
	"quests_completed",
	"posts_created",
	"comments_created",
	"likes_received",
	"streak_days",
	"xp_total",
	"level_reached",
	"approved_submissions",
}


class AdminBadgeItem(BaseModel):
	id: uuid.UUID
	name: str
	description: str
	icon_url: str
	rarity: str
	category: str
	criteria: dict
	is_hidden: bool
	is_active: bool
	sort_order: int
	created_at: datetime
	updated_at: datetime

	model_config = {"from_attributes": True}


class AdminBadgeListResponse(PaginatedResponse[AdminBadgeItem]):
	pass


class AdminBadgeConditionType(BaseModel):
	value: str
	label: str
	description: str


class AdminBadgeConditionTypesResponse(BaseModel):
	items: list[AdminBadgeConditionType]


class AdminBadgeCreateRequest(BaseModel):
	name: str = Field(min_length=2, max_length=100)
	description: str = Field(min_length=1, max_length=1000)
	icon_url: str = Field(min_length=1, max_length=255)
	rarity: str = Field(default="common", max_length=30)
	category: str = Field(default="general", max_length=50)
	condition_type: str
	target: int = Field(ge=1, le=1_000_000)
	is_hidden: bool = False
	is_active: bool = True
	sort_order: int = Field(default=0, ge=0, le=100000)


class AdminBadgeUpdateRequest(BaseModel):
	name: Optional[str] = Field(default=None, min_length=2, max_length=100)
	description: Optional[str] = Field(default=None, min_length=1, max_length=1000)
	icon_url: Optional[str] = Field(default=None, min_length=1, max_length=255)
	rarity: Optional[str] = Field(default=None, max_length=30)
	category: Optional[str] = Field(default=None, max_length=50)
	condition_type: Optional[str] = None
	target: Optional[int] = Field(default=None, ge=1, le=1_000_000)
	is_hidden: Optional[bool] = None
	is_active: Optional[bool] = None
	sort_order: Optional[int] = Field(default=None, ge=0, le=100000)


# ── POI ───────────────────────────────────────────────────────────────────────

class AdminPoiItem(BaseModel):
	id: uuid.UUID
	name: str
	poi_type: str
	latitude: float
	longitude: float
	radius_m: float
	source: str
	external_id: str
	external_type: Optional[str] = None
	is_active: bool
	created_at: datetime

	model_config = {"from_attributes": True}


class AdminPoiListResponse(BaseModel):
	items: list[AdminPoiItem]
	total: int


class AdminPoiCreateRequest(BaseModel):
	name: str = Field(max_length=255)
	poi_type: str = Field(max_length=50)
	latitude: float = Field(ge=-90, le=90)
	longitude: float = Field(ge=-180, le=180)
	radius_m: float = Field(gt=0, le=10000)
	source: str = Field(default="admin", max_length=20)
	external_id: Optional[str] = Field(default=None, max_length=64)
	external_type: Optional[str] = Field(default=None, max_length=20)


class AdminPoiUpdateRequest(BaseModel):
	name: Optional[str] = Field(default=None, max_length=255)
	poi_type: Optional[str] = Field(default=None, max_length=50)
	latitude: Optional[float] = Field(default=None, ge=-90, le=90)
	longitude: Optional[float] = Field(default=None, ge=-180, le=180)
	radius_m: Optional[float] = Field(default=None, gt=0, le=10000)
	is_active: Optional[bool] = None
