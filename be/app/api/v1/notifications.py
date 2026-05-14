from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import CurrentUser, get_current_user
from app.deps.db import get_db
from app.schemas.notification import (
	NotificationActionResponse,
	NotificationListResponse,
	PushTokenRegisterRequest,
	PushTokenUnregisterRequest,
	UnreadCountResponse,
)
from app.services.notification.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
	return NotificationService(db)


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=30, ge=1, le=100),
	current_user: CurrentUser = Depends(get_current_user),
	service: NotificationService = Depends(get_notification_service),
) -> NotificationListResponse:
	return await service.list_notifications(user_id=current_user.id, page=page, page_size=page_size)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
	current_user: CurrentUser = Depends(get_current_user),
	service: NotificationService = Depends(get_notification_service),
) -> UnreadCountResponse:
	return await service.unread_count(user_id=current_user.id)


@router.patch("/{notification_id}/read", response_model=NotificationActionResponse)
async def mark_read(
	notification_id: UUID,
	current_user: CurrentUser = Depends(get_current_user),
	service: NotificationService = Depends(get_notification_service),
) -> NotificationActionResponse:
	return await service.mark_read(user_id=current_user.id, notification_id=notification_id)


@router.patch("/read-all", response_model=NotificationActionResponse)
async def mark_all_read(
	current_user: CurrentUser = Depends(get_current_user),
	service: NotificationService = Depends(get_notification_service),
) -> NotificationActionResponse:
	return await service.mark_all_read(user_id=current_user.id)


@router.post("/push-tokens", response_model=NotificationActionResponse)
async def register_push_token(
	payload: PushTokenRegisterRequest,
	current_user: CurrentUser = Depends(get_current_user),
	service: NotificationService = Depends(get_notification_service),
) -> NotificationActionResponse:
	return await service.register_push_token(user_id=current_user.id, payload=payload)


@router.post("/push-tokens/unregister", response_model=NotificationActionResponse)
async def unregister_push_token(
	payload: PushTokenUnregisterRequest,
	current_user: CurrentUser = Depends(get_current_user),
	service: NotificationService = Depends(get_notification_service),
) -> NotificationActionResponse:
	return await service.unregister_push_token(user_id=current_user.id, token=payload.token)
