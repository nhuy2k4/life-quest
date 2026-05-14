from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import CurrentUser, get_current_user
from app.deps.db import get_db
from app.schemas.gamification import XpHistoryResponse
from app.services.gamification.xp_history_service import XpHistoryService

router = APIRouter(prefix="/gamification", tags=["Gamification"])


def get_xp_history_service(db: AsyncSession = Depends(get_db)) -> XpHistoryService:
	return XpHistoryService(db)


@router.get("/xp-history", response_model=XpHistoryResponse)
async def get_xp_history(
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	current_user: CurrentUser = Depends(get_current_user),
	service: XpHistoryService = Depends(get_xp_history_service),
) -> XpHistoryResponse:
	return await service.get_xp_history(user_id=current_user.id, page=page, page_size=page_size)
