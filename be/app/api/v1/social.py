import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
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
	PostUpdateRequest,
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


@router.get("/posts/{post_id}", response_model=PostResponse)
async def get_post(
	post_id: uuid.UUID,
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> PostResponse:
	return await service.get_post_by_id(user_id=current_user.id, post_id=post_id)


@router.patch("/posts/{post_id}", response_model=PostResponse)
async def update_post(
	post_id: uuid.UUID,
	payload: PostUpdateRequest,
	current_user: CurrentUser = Depends(get_current_user),
	service: SocialService = Depends(get_social_service),
) -> PostResponse:
	return await service.update_post(user_id=current_user.id, post_id=post_id, payload=payload)



@router.get("/posts/{post_id}/share", response_class=HTMLResponse)
async def share_post_redirect(post_id: uuid.UUID) -> HTMLResponse:
	html_content = f"""
	<!DOCTYPE html>
	<html>
	<head>
	  <meta charset="utf-8">
	  <meta name="viewport" content="width=device-width, initial-scale=1">
	  <title>Mở bài viết trong LifeQuest</title>
	  <style>
		body {{
		  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
		  display: flex;
		  flex-direction: column;
		  align-items: center;
		  justify-content: center;
		  height: 100vh;
		  margin: 0;
		  background-color: #F9FAFB;
		  color: #11181C;
		  padding: 20px;
		  box-sizing: border-box;
		}}
		.container {{
		  text-align: center;
		  max-width: 400px;
		  background: white;
		  padding: 30px;
		  border-radius: 16px;
		  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
		}}
		h1 {{
		  font-size: 20px;
		  margin-bottom: 10px;
		}}
		p {{
		  color: #6B7280;
		  font-size: 14px;
		  margin-bottom: 24px;
		  line-height: 1.5;
		}}
		.btn {{
		  display: inline-block;
		  background-color: #6366F1;
		  color: white;
		  padding: 12px 24px;
		  border-radius: 8px;
		  text-decoration: none;
		  font-weight: 600;
		  font-size: 15px;
		  transition: background-color 0.2s;
		}}
		.btn:hover {{
		  background-color: #4F46E5;
		}}
	  </style>
	  <script>
		window.onload = function() {{
		  var appUrl = "lifequestmobile://post-detail?postId={post_id}";
		  window.location.href = appUrl;
		  setTimeout(function() {{
			window.location.replace(appUrl);
		  }}, 500);
		}};
	  </script>
	</head>
	<body>
	  <div class="container">
		<h1>Đang mở LifeQuest...</h1>
		<p>Nếu ứng dụng không tự động mở, hãy bấm vào nút bên dưới để xem bài viết.</p>
		<a class="btn" href="lifequestmobile://post-detail?postId={post_id}">Mở ứng dụng LifeQuest</a>
	  </div>
	</body>
	</html>
	"""
	return HTMLResponse(content=html_content)


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
