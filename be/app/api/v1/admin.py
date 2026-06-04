from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import CurrentUser, require_admin
from app.deps.db import get_db
from app.schemas.admin import (
	AdminCommentActionResponse,
	AdminQuestListResponse,
	AdminQuestUpdateRequest,
	AdminPostActionResponse,
	AdminPostListResponse,
	AdminUserBanRequest,
	AdminUserListResponse,
	AdminUserUpdateRequest,
	AdminUserXpAdjustRequest,
	AdminUserXpAdjustResponse,
	AdminCommentListResponse,
	AdminPoiItem,
	AdminPoiListResponse,
	AdminPoiCreateRequest,
	AdminPoiUpdateRequest,
	AdminBadgeItem,
	AdminBadgeListResponse,
	AdminBadgeCreateRequest,
	AdminBadgeUpdateRequest,
	AdminBadgeConditionTypesResponse,
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


@router.patch("/users/{user_id}", response_model=AdminPostActionResponse)
async def update_user(
	user_id: UUID,
	payload: AdminUserUpdateRequest,
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminPostActionResponse:
	await service.update_user(user_id=user_id, payload=payload)
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


@router.get("/posts", response_model=AdminPostListResponse)
async def list_posts(
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	q: str | None = Query(default=None, min_length=1),
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminPostListResponse:
	return await service.list_posts(page=page, page_size=page_size, query=q)


@router.get("/posts/{post_id}/comments", response_model=AdminCommentListResponse)
async def list_post_comments(
	post_id: UUID,
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=200),
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminCommentListResponse:
	return await service.list_post_comments(post_id=post_id, page=page, page_size=page_size)


@router.delete("/comments/{comment_id}", response_model=AdminCommentActionResponse)
async def delete_comment(
	comment_id: UUID,
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminCommentActionResponse:
	await service.delete_comment(comment_id=comment_id)
	return AdminCommentActionResponse()


@router.get("/badges", response_model=AdminBadgeListResponse)
async def list_badges(
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=50, ge=1, le=200),
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminBadgeListResponse:
	return await service.list_badges(page=page, page_size=page_size)


@router.get("/badges/condition-types", response_model=AdminBadgeConditionTypesResponse)
async def list_badge_condition_types(
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminBadgeConditionTypesResponse:
	return service.list_badge_condition_types()


@router.post("/badges", response_model=AdminBadgeItem, status_code=status.HTTP_201_CREATED)
async def create_badge(
	payload: AdminBadgeCreateRequest,
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminBadgeItem:
	return await service.create_badge(payload=payload)


@router.patch("/badges/{badge_id}", response_model=AdminBadgeItem)
async def update_badge(
	badge_id: UUID,
	payload: AdminBadgeUpdateRequest,
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminBadgeItem:
	return await service.update_badge(badge_id=badge_id, payload=payload)


@router.delete("/badges/{badge_id}", response_model=AdminPostActionResponse)
async def delete_badge(
	badge_id: UUID,
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminPostActionResponse:
	await service.delete_badge(badge_id=badge_id)
	return AdminPostActionResponse()


# ── POI endpoints ─────────────────────────────────────────────────────────────

@router.get("/pois", response_model=AdminPoiListResponse)
async def list_pois(
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=500, ge=1, le=1000),
	active_only: bool = Query(default=False),
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminPoiListResponse:
	return await service.list_pois(page=page, page_size=page_size, active_only=active_only)


@router.post("/pois", response_model=AdminPoiItem, status_code=status.HTTP_201_CREATED)
async def create_poi(
	payload: AdminPoiCreateRequest,
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminPoiItem:
	return await service.create_poi(payload=payload)


@router.patch("/pois/{poi_id}", response_model=AdminPoiItem)
async def update_poi(
	poi_id: UUID,
	payload: AdminPoiUpdateRequest,
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminPoiItem:
	return await service.update_poi(poi_id=poi_id, payload=payload)


@router.delete("/pois/{poi_id}", response_model=AdminPostActionResponse)
async def delete_poi(
	poi_id: UUID,
	_admin: CurrentUser = Depends(require_admin),
	service: AdminService = Depends(get_admin_service),
) -> AdminPostActionResponse:
	await service.delete_poi(poi_id=poi_id)
	return AdminPostActionResponse()
