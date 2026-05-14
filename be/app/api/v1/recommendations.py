from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import CurrentUser, get_current_user
from app.deps.db import get_db
from app.schemas.recommendation import (
	RecommendationListResponse,
	RecommendationLogRequest,
	RecommendationLogResponse,
)
from app.services.recommendation.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


def get_recommendation_service(db: AsyncSession = Depends(get_db)) -> RecommendationService:
	return RecommendationService(db)


@router.get("/quests", response_model=RecommendationListResponse)
async def get_recommended_quests(
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	lat: float | None = Query(default=None),
	lng: float | None = Query(default=None),
	current_user: CurrentUser = Depends(get_current_user),
	service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationListResponse:
	return await service.get_recommended_quests(
		user_id=current_user.id,
		onboarding_completed=current_user.onboarding_completed,
		page=page,
		page_size=page_size,
		lat=lat,
		lng=lng,
	)



@router.post("/log", response_model=RecommendationLogResponse)
async def log_recommendation_event(
	payload: RecommendationLogRequest,
	current_user: CurrentUser = Depends(get_current_user),
	service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationLogResponse:
	await service.log_event(user_id=current_user.id, payload=payload)
	return RecommendationLogResponse()
