from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import CurrentUser, require_admin
from app.deps.db import get_db
from app.schemas.admin import (
	AdminCommentActionResponse,
	AdminQuestListResponse,
	AdminQuestUpdateRequest,
	AdminPostActionResponse,
	AdminUserBanRequest,
	AdminUserListResponse,
	AdminUserXpAdjustRequest,
	AdminUserXpAdjustResponse,
)
from app.services.admin.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin"])


def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminService:
	return AdminService(db)


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminUserListResponse:
	return await service.list_users(page=page, page_size=page_size)


@router.patch("/users/{user_id}/ban", response_model=AdminPostActionResponse)
async def ban_user(
	user_id: UUID,
	payload: AdminUserBanRequest,
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminPostActionResponse:
	await service.set_user_ban(user_id=user_id, is_banned=payload.is_banned)
	return AdminPostActionResponse()


@router.post("/users/{user_id}/xp-adjust", response_model=AdminUserXpAdjustResponse)
async def adjust_user_xp(
	user_id: UUID,
	payload: AdminUserXpAdjustRequest,
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminUserXpAdjustResponse:
	return await service.adjust_user_xp(user_id=user_id, payload=payload)


@router.get("/quests", response_model=AdminQuestListResponse)
async def list_quests(
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminQuestListResponse:
	return await service.list_quests(page=page, page_size=page_size)


@router.patch("/quests/{quest_id}", response_model=AdminPostActionResponse)
async def update_quest(
	quest_id: UUID,
	payload: AdminQuestUpdateRequest,
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminPostActionResponse:
	await service.update_quest(quest_id=quest_id, payload=payload)
	return AdminPostActionResponse()


@router.delete("/posts/{post_id}", response_model=AdminPostActionResponse)
async def delete_post(
	post_id: UUID,
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminPostActionResponse:
	await service.delete_post(post_id=post_id)
	return AdminPostActionResponse()


@router.delete("/comments/{comment_id}", response_model=AdminCommentActionResponse)
async def delete_comment(
	comment_id: UUID,
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminCommentActionResponse:
	await service.delete_comment(comment_id=comment_id)
	return AdminCommentActionResponse()
