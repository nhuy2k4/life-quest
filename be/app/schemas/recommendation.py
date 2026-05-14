import uuid
from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.common import PaginatedResponse
from app.schemas.quest import QuestUserStatus


class RecommendationReasonCode(StrEnum):
    MATCH_CATEGORY = "match_category"
    FIT_ACTIVITY_LEVEL = "fit_activity_level"
    ONBOARDING_EASY = "onboarding_easy"
    IN_PROGRESS = "in_progress"
    HIGH_XP = "high_xp"
    LOCATION_REQUIRED = "location_required"
    FRIENDS_COMPLETED = "friends_completed"
    FRESH = "fresh"
    TRENDING = "trending"
    EXPLORATION = "exploration"
    NEARBY = "nearby"



class RecommendationEventType(StrEnum):
    SHOWN = "shown"
    CLICKED = "clicked"
    STARTED = "started"
    COMPLETED = "completed"
    IGNORED = "ignored"


class RecommendationScoreBreakdown(BaseModel):
    base_score: float = 0.0
    status_score: float = 0.0
    category_score: float = 0.0
    difficulty_score: float = 0.0
    xp_score: float = 0.0
    social_score: float = 0.0
    freshness_score: float = 0.0
    location_penalty: float = 0.0
    repetition_penalty: float = 0.0
    diversity_penalty: float = 0.0
    rule_score: float = 0.0
    ml_score: float = 0.0
    final_score: float = 0.0


class RecommendationQuestItem(BaseModel):
    id: uuid.UUID
    rendered_text: str
    title: str
    description: str | None = None
    difficulty: str = "medium"
    image_url: str | None = None
    labels: list[str]
    min_confidence: float
    poi_required: bool
    xp_reward: int
    user_status: QuestUserStatus = "not_started"
    recommendation_score: float
    ml_score: float | None = None
    reasons: list[RecommendationReasonCode] = Field(default_factory=list)
    score_breakdown: RecommendationScoreBreakdown | None = None



class RecommendationListResponse(PaginatedResponse[RecommendationQuestItem]):
    request_id: uuid.UUID

    @classmethod
    def create(
        cls,
        *,
        items: list[RecommendationQuestItem],
        total: int,
        page: int,
        page_size: int,
        request_id: uuid.UUID,
    ) -> "RecommendationListResponse":
        has_next = (page * page_size) < total
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next,
            request_id=request_id,
        )


class RecommendationLogRequest(BaseModel):
    request_id: uuid.UUID
    quest_id: uuid.UUID
    event: RecommendationEventType
    rank: int | None = None
    score: float | None = None
    rule_score: float | None = None
    ml_score: float | None = None
    final_score: float | None = None
    reasons: list[RecommendationReasonCode] = Field(default_factory=list)
    score_breakdown: RecommendationScoreBreakdown | None = None
    features_snapshot: dict[str, float] | None = None


class RecommendationLogResponse(BaseModel):
    status: str = "ok"
