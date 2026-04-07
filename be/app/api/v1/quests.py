from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import CurrentUser, get_current_user
from app.deps.db import get_db
from app.repositories.quest_repository import QuestRepository
from app.schemas.common import PaginatedResponse
from app.schemas.quest import (
	QuestDetailResponse,
	QuestListItemResponse,
	StartQuestResponse,
	SubmitQuestRequest,
	SubmitQuestResponse,
)
from app.services.quest.quest_service import QuestService

router = APIRouter(prefix="/quests", tags=["Quests"])


def get_quest_service(db: AsyncSession = Depends(get_db)) -> QuestService:
	return QuestService(QuestRepository(db))


@router.get(
	"",
	response_model=PaginatedResponse[QuestListItemResponse],
	summary="Danh sách quest đang hoạt động",
)
async def list_quests(
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	current_user: CurrentUser = Depends(get_current_user),
	service: QuestService = Depends(get_quest_service),
) -> PaginatedResponse[QuestListItemResponse]:
	items, total = await service.list_quests(
		user_id=current_user.id,
		page=page,
		page_size=page_size,
	)
	return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.get(
	"/{quest_id}",
	response_model=QuestDetailResponse,
	summary="Chi tiết quest",
)
async def get_quest_detail(
	quest_id: UUID,
	current_user: CurrentUser = Depends(get_current_user),
	service: QuestService = Depends(get_quest_service),
) -> QuestDetailResponse:
	return await service.get_quest_detail(user_id=current_user.id, quest_id=quest_id)


@router.post(
	"/{quest_id}/start",
	response_model=StartQuestResponse,
	status_code=status.HTTP_201_CREATED,
	summary="Bắt đầu quest",
)
async def start_quest(
	quest_id: UUID,
	current_user: CurrentUser = Depends(get_current_user),
	service: QuestService = Depends(get_quest_service),
) -> StartQuestResponse:
	return await service.start_quest(
		user_id=current_user.id,
		onboarding_completed=current_user.onboarding_completed,
		quest_id=quest_id,
	)


@router.post(
	"/{quest_id}/submit",
	response_model=SubmitQuestResponse,
	status_code=status.HTTP_201_CREATED,
	summary="Nộp bằng chứng hoàn thành quest",
)
async def submit_quest(
	quest_id: UUID,
	payload: SubmitQuestRequest,
	current_user: CurrentUser = Depends(get_current_user),
	service: QuestService = Depends(get_quest_service),
) -> SubmitQuestResponse:
	return await service.submit_quest(
		user_id=current_user.id,
		onboarding_completed=current_user.onboarding_completed,
		quest_id=quest_id,
		payload=payload,
	)
