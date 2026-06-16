import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import CurrentUser, get_current_user
from app.deps.db import get_db
from app.schemas.social import (
	CommentCreateRequest,
	CommentListResponse,
	FeedResponse,
	FollowListResponse,
	FollowResponse,
	LikeResponse,
	PostCreateRequest,
	PostResponse,
)
from app.services.social.social_service import SocialService


router = APIRouter(prefix="/social", tags=["Social"])


def get_social_service(db: AsyncSession = Depends(get_db)) -> SocialService:
	return SocialService(db)


@router.get("/feed", response_model=FeedResponse)
async def get_feed(
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	scope: str = Query(default="all", pattern="^(all|following)$"),
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> FeedResponse:
	return await service.get_feed(user_id=current_user.id, page=page, page_size=page_size, scope=scope)


@router.get("/search", response_model=FeedResponse)
async def search_posts(
	q: str = Query(min_length=1, max_length=80),
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> FeedResponse:
	return await service.search_posts(user_id=current_user.id, query=q, page=page, page_size=page_size)


@router.post("/posts", response_model=PostResponse)
async def create_post(
	payload: PostCreateRequest,
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> PostResponse:
	return await service.create_post(user_id=current_user.id, payload=payload)


@router.delete("/posts/{post_id}", response_model=FollowResponse)
async def delete_post(
	post_id: uuid.UUID,
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> FollowResponse:
	await service.delete_post(user_id=current_user.id, post_id=post_id)
	return FollowResponse()


@router.post("/posts/{post_id}/like", response_model=LikeResponse)
async def like_post(
	post_id: uuid.UUID,
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> LikeResponse:
	await service.like_post(user_id=current_user.id, post_id=post_id)
	return LikeResponse()


@router.delete("/posts/{post_id}/like", response_model=LikeResponse)
async def unlike_post(
	post_id: uuid.UUID,
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> LikeResponse:
	await service.unlike_post(user_id=current_user.id, post_id=post_id)
	return LikeResponse()


@router.post("/posts/{post_id}/comments", response_model=PostResponse)
async def add_comment(
	post_id: uuid.UUID,
	payload: CommentCreateRequest,
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> PostResponse:
	return await service.add_comment(user_id=current_user.id, post_id=post_id, payload=payload)


@router.get("/posts/{post_id}/comments", response_model=CommentListResponse)
async def list_comments(
	post_id: uuid.UUID,
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> CommentListResponse:
	return await service.list_comments(
		user_id=current_user.id,
		post_id=post_id,
		page=page,
		page_size=page_size,
	)


@router.delete("/comments/{comment_id}", response_model=FollowResponse)
async def delete_comment(
	comment_id: uuid.UUID,
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> FollowResponse:
	await service.delete_comment(user_id=current_user.id, comment_id=comment_id)
	return FollowResponse()


@router.post("/users/{target_user_id}/follow", response_model=FollowResponse)
async def follow_user(
	target_user_id: uuid.UUID,
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> FollowResponse:
	await service.follow_user(follower_id=current_user.id, following_id=target_user_id)
	return FollowResponse()


@router.delete("/users/{target_user_id}/follow", response_model=FollowResponse)
async def unfollow_user(
	target_user_id: uuid.UUID,
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> FollowResponse:
	await service.unfollow_user(follower_id=current_user.id, following_id=target_user_id)
	return FollowResponse()


@router.get("/users/{target_user_id}/followers", response_model=FollowListResponse)
async def list_followers(
	target_user_id: uuid.UUID,
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> FollowListResponse:
	return await service.list_followers(
		user_id=current_user.id,
		target_user_id=target_user_id,
		page=page,
		page_size=page_size,
	)


@router.get("/users/{target_user_id}/following", response_model=FollowListResponse)
async def list_following(
	target_user_id: uuid.UUID,
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> FollowListResponse:
	return await service.list_following(
		user_id=current_user.id,
		target_user_id=target_user_id,
		page=page,
		page_size=page_size,
	)


@router.get("/users/{target_user_id}/friends", response_model=FollowListResponse)
async def list_friends(
	target_user_id: uuid.UUID,
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> FollowListResponse:
	return await service.list_friends(
		user_id=current_user.id,
		target_user_id=target_user_id,
		page=page,
		page_size=page_size,
	)


@router.get("/users/{target_user_id}/awards", response_model=FeedResponse)
async def get_user_awards(
	target_user_id: uuid.UUID,
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> FeedResponse:
	return await service.get_user_awards(
		user_id=current_user.id,
		target_user_id=target_user_id,
		page=page,
		page_size=page_size,
	)
