import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import CurrentUser, get_current_user, require_admin
from app.deps.db import get_db
from app.schemas.event import (
	EventActionResponse,
	EventCreateRequest,
	EventDetailResponse,
	EventLeaderboardResponse,
	EventListItem,
	EventPostListResponse,
	EventUpdateRequest,
)
from app.models.enums import UserRole
from app.services.event.event_service import EventService


router = APIRouter(prefix="/events", tags=["Events"])


def get_event_service(db: AsyncSession = Depends(get_db)) -> EventService:
	return EventService(db)


@router.get("", response_model=list[EventListItem])
async def list_events(
	status_filter: str | None = Query(default=None, alias="status", pattern="^(draft|active|ended)$"),
	current_user: CurrentUser = Depends(get_current_user),
	service: EventService = Depends(get_event_service),
) -> list[EventListItem]:
	is_admin = current_user.role == UserRole.ADMIN
	return await service.list_events(status=status_filter, is_admin=is_admin)


@router.post("", response_model=EventDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
	payload: EventCreateRequest,
	admin: CurrentUser = Depends(require_admin),
	service: EventService = Depends(get_event_service),
) -> EventDetailResponse:
	return await service.create_event(actor_id=admin.id, payload=payload)


@router.get("/{event_id}", response_model=EventDetailResponse)
async def get_event_detail(
	event_id: uuid.UUID,
	current_user: CurrentUser = Depends(get_current_user),
	service: EventService = Depends(get_event_service),
) -> EventDetailResponse:
	return await service.get_event_detail(event_id=event_id, user_id=current_user.id)


@router.patch("/{event_id}", response_model=EventDetailResponse)
async def update_event(
	event_id: uuid.UUID,
	payload: EventUpdateRequest,
	_admin: CurrentUser = Depends(require_admin),
	service: EventService = Depends(get_event_service),
) -> EventDetailResponse:
	return await service.update_event(event_id=event_id, payload=payload)


@router.post("/{event_id}/end", response_model=EventActionResponse)
async def end_event(
	event_id: uuid.UUID,
	_admin: CurrentUser = Depends(require_admin),
	service: EventService = Depends(get_event_service),
) -> EventActionResponse:
	return await service.end_event(event_id=event_id)


@router.get("/{event_id}/leaderboard", response_model=EventLeaderboardResponse)
async def get_event_leaderboard(
	event_id: uuid.UUID,
	limit: int = Query(default=5, ge=1, le=50),
	_current_user: CurrentUser = Depends(get_current_user),
	service: EventService = Depends(get_event_service),
) -> EventLeaderboardResponse:
	return await service.get_leaderboard(event_id=event_id, limit=limit)


@router.get("/{event_id}/posts", response_model=EventPostListResponse)
async def list_event_posts(
	event_id: uuid.UUID,
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	current_user: CurrentUser = Depends(get_current_user),
	service: EventService = Depends(get_event_service),
) -> EventPostListResponse:
	items, total = await service.list_event_posts(
		event_id=event_id,
		user_id=current_user.id,
		page=page,
		page_size=page_size,
	)
	return EventPostListResponse.create(items=items, total=total, page=page, page_size=page_size)
