import uuid
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.quest import QuestUserStatus
from app.schemas.social import PostResponse


class RecommendationEventType(StrEnum):
	SHOWN = "shown"
	CLICKED = "clicked"
	STARTED = "started"
	COMPLETED = "completed"
	IGNORED = "ignored"
	POST_LIKED = "post_liked"
	POST_COMMENTED = "post_commented"


class RecommendationSectionKey(StrEnum):
	RECOMMENDED_FOR_YOU = "recommended_for_you"
	TRENDING_NEAR_YOU = "trending_near_you"
	CONTINUE_YOUR_MISSIONS = "continue_your_missions"
	EXPLORE_NEW_THINGS = "explore_new_things"


class RecommendationScoreBreakdown(BaseModel):
	model_config = ConfigDict(populate_by_name=True)

	interest: float = 0.0
	nearby: float = 0.0
	trending: float = 0.0
	continue_score: float = Field(default=0.0, alias="continue")
	affinity: float = 0.0
	anti_repeat: float = 0.0
	exploration: float = 0.0
	freshness: float = 0.0


class RecommendationDebugInfo(BaseModel):
	sources: list[str] = Field(default_factory=list)
	matched_categories: list[str] = Field(default_factory=list)
	nearby_distance_m: float | None = None
	poi_id: uuid.UUID | None = None
	poi_name: str | None = None
	popularity_score: float = 0.0
	affinity_score: float = 0.0
	was_recently_shown: bool = False
	rank_notes: list[str] = Field(default_factory=list)


class RecommendationQuestItem(BaseModel):
	id: uuid.UUID
	rendered_text: str
	title: str
	description: str | None = None
	difficulty: str = "medium"
	image_url: str | None = None
	poi_id: uuid.UUID | None = None
	poi_name: str | None = None
	nearby_distance_m: float | None = None
	labels: list[str]
	min_confidence: float
	xp_reward: int
	user_status: QuestUserStatus = "not_started"
	final_score: float
	reasons: list[str] = Field(default_factory=list)
	score_breakdown: RecommendationScoreBreakdown
	debug: RecommendationDebugInfo | None = None


class RecommendationPostItem(PostResponse):
	final_score: float
	reasons: list[str] = Field(default_factory=list)


class RecommendationSection(BaseModel):
	key: RecommendationSectionKey
	title: str
	item_type: str = "quest"
	items: list[RecommendationQuestItem | RecommendationPostItem]


class RecommendationListResponse(BaseModel):
	request_id: uuid.UUID
	sections: list[RecommendationSection]
	for_you_posts: list[RecommendationPostItem]
	explore_quests: list[RecommendationQuestItem]
	recommended_for_you: list[RecommendationPostItem]
	trending_near_you: list[RecommendationQuestItem]
	continue_your_missions: list[RecommendationQuestItem]
	explore_new_things: list[RecommendationQuestItem]


class RecommendationEventRequest(BaseModel):
	request_id: uuid.UUID
	quest_id: uuid.UUID | None = None
	post_id: uuid.UUID | None = None
	event: RecommendationEventType
	section: RecommendationSectionKey | None = None
	rank: int | None = None
	final_score: float | None = None
	score: float | None = None
	reasons: list[str] = Field(default_factory=list)
	score_breakdown: RecommendationScoreBreakdown | None = None


class RecommendationLogRequest(RecommendationEventRequest):
	"""Deprecated compatibility payload for POST /recommendations/log."""


class RecommendationLogResponse(BaseModel):
	status: str = "ok"
