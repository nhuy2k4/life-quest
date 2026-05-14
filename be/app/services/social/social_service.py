import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, ConflictException, ForbiddenException, NotFoundException
from app.models.social import Comment, Follow, Like, Post
from app.models.submission import Submission
from app.models.user import User
from app.models.user_quest import UserQuest
from app.schemas.common import PaginatedResponse
from app.schemas.social import (
	CommentCreateRequest,
	CommentListResponse,
	CommentResponse,
	FeedResponse,
	FollowListResponse,
	PostCreateRequest,
	PostQuestInfo,
	PostResponse,
)
from app.schemas.user import UserPublicResponse
from app.services.notification.notification_service import NotificationService


class SocialService:
	def __init__(self, db: AsyncSession) -> None:
		self.db = db

	async def get_feed(self, *, user_id: uuid.UUID, page: int, page_size: int) -> FeedResponse:
		offset = (page - 1) * page_size

		# GLOBAL FEED: Fetch all posts for dev demo discovery
		total = await self.db.scalar(
			select(func.count()).select_from(Post)
		)
		rows = await self.db.scalars(
			select(Post)
			.options(
				selectinload(Post.user),
				selectinload(Post.submission).selectinload(Submission.user_quest).selectinload(UserQuest.quest),
				selectinload(Post.quest),
			)
			.order_by(Post.created_at.desc())
			.offset(offset)
			.limit(page_size)
		)
		posts = rows.all()


		liked_post_ids = await self._get_liked_post_ids(user_id=user_id, post_ids=[post.id for post in posts])
		items = [self._to_post_response(post, liked_by_me=post.id in liked_post_ids) for post in posts]

		return FeedResponse.create(
			items=items,
			total=int(total or 0),
			page=page,
			page_size=page_size,
		)

	async def create_post(self, *, user_id: uuid.UUID, payload: PostCreateRequest) -> PostResponse:
		if payload.submission_id:
			existing_post = await self._get_post_by_submission(
				user_id=user_id,
				submission_id=payload.submission_id,
			)
			if existing_post is not None:
				return self._to_post_response(existing_post, liked_by_me=False)

			submission = await self.db.scalar(
				select(Submission)
				.join(UserQuest, Submission.user_quest_id == UserQuest.id)
				.where(Submission.id == payload.submission_id, UserQuest.user_id == user_id)
			)
			if submission is None:
				raise NotFoundException("Submission không tồn tại hoặc không thuộc về bạn")
			post = Post(user_id=user_id, submission_id=payload.submission_id, caption=payload.caption)
		else:
			post = Post(
				user_id=user_id, 
				image_url=payload.image_url, 
				caption=payload.caption,
				quest_id=payload.quest_id
			)

		self.db.add(post)
		try:
			await self.db.commit()
		except IntegrityError as exc:
			await self.db.rollback()
			if payload.submission_id:
				existing_post = await self._get_post_by_submission(
					user_id=user_id,
					submission_id=payload.submission_id,
				)
				if existing_post is not None:
					return self._to_post_response(existing_post, liked_by_me=False)
			raise ConflictException("Lỗi khi tạo post") from exc

		stored = await self._get_post(post.id)
		if stored is None:
			raise NotFoundException("Post không tồn tại")
		return self._to_post_response(stored, liked_by_me=False)

	async def delete_post(self, *, user_id: uuid.UUID, post_id: uuid.UUID) -> None:
		post = await self.db.scalar(select(Post).where(Post.id == post_id))
		if post is None:
			raise NotFoundException("Post không tồn tại")
		if post.user_id != user_id:
			raise ForbiddenException("Bạn không có quyền xóa post này")

		await self.db.delete(post)
		await self.db.commit()

	async def like_post(self, *, user_id: uuid.UUID, post_id: uuid.UUID) -> None:
		post = await self.db.scalar(select(Post).where(Post.id == post_id))
		if post is None:
			raise NotFoundException("Post không tồn tại")

		self.db.add(Like(user_id=user_id, post_id=post_id))
		try:
			await self.db.flush()
		except IntegrityError as exc:
			await self.db.rollback()
			return

		await self.db.execute(
			update(Post)
			.where(Post.id == post_id)
			.values(like_count=Post.like_count + 1)
		)
		if post.user_id != user_id:
			actor = await self.db.scalar(select(User).where(User.id == user_id))
			await NotificationService(self.db).create_notification(
				user_id=post.user_id,
				notification_type="like",
				data={
					"post_id": str(post_id),
					"actor_id": str(user_id),
					"actor_username": actor.username if actor else None,
				},
			)
		await self.db.commit()

	async def unlike_post(self, *, user_id: uuid.UUID, post_id: uuid.UUID) -> None:
		result = await self.db.execute(
			delete(Like).where(Like.user_id == user_id, Like.post_id == post_id)
		)
		if result.rowcount == 0:
			return

		await self.db.execute(
			update(Post)
			.where(Post.id == post_id)
			.values(like_count=func.greatest(Post.like_count - 1, 0))
		)
		await self.db.commit()

	async def add_comment(
		self,
		*,
		user_id: uuid.UUID,
		post_id: uuid.UUID,
		payload: CommentCreateRequest,
	) -> PostResponse:
		post = await self.db.scalar(select(Post).where(Post.id == post_id))
		if post is None:
			raise NotFoundException("Post không tồn tại")

		if payload.parent_id:
			parent = await self.db.scalar(select(Comment).where(Comment.id == payload.parent_id))
			if parent is None or parent.post_id != post_id:
				raise BadRequestException("Parent comment không hợp lệ")

		comment = Comment(
			post_id=post_id,
			user_id=user_id,
			parent_id=payload.parent_id,
			content=payload.content.strip(),
		)
		self.db.add(comment)
		await self.db.execute(
			update(Post)
			.where(Post.id == post_id)
			.values(comment_count=Post.comment_count + 1)
		)
		if post.user_id != user_id:
			actor = await self.db.scalar(select(User).where(User.id == user_id))
			await NotificationService(self.db).create_notification(
				user_id=post.user_id,
				notification_type="comment",
				data={
					"post_id": str(post_id),
					"comment_id": str(comment.id),
					"actor_id": str(user_id),
					"actor_username": actor.username if actor else None,
					"comment_preview": comment.content[:120],
				},
			)
		await self.db.commit()

		stored = await self._get_post(post_id)
		if stored is None:
			raise NotFoundException("Post không tồn tại")
		return self._to_post_response(stored, liked_by_me=False)

	async def list_comments(
		self,
		*,
		user_id: uuid.UUID,
		post_id: uuid.UUID,
		page: int,
		page_size: int,
	) -> CommentListResponse:
		offset = (page - 1) * page_size
		total = await self.db.scalar(
			select(func.count()).select_from(Comment).where(Comment.post_id == post_id)
		)
		rows = await self.db.scalars(
			select(Comment)
			.options(selectinload(Comment.user))
			.where(Comment.post_id == post_id)
			.order_by(Comment.created_at.asc())
			.offset(offset)
			.limit(page_size)
		)
		comments = rows.all()

		items = [self._to_comment_response(comment) for comment in comments]
		return CommentListResponse.create(
			items=items,
			total=int(total or 0),
			page=page,
			page_size=page_size,
		)

	async def delete_comment(self, *, user_id: uuid.UUID, comment_id: uuid.UUID) -> None:
		comment = await self.db.scalar(select(Comment).where(Comment.id == comment_id))
		if comment is None:
			raise NotFoundException("Comment không tồn tại")
		if comment.user_id != user_id:
			raise ForbiddenException("Bạn không có quyền xóa comment này")

		if not comment.is_deleted:
			comment.is_deleted = True
			comment.content = ""
			await self.db.execute(
				update(Post)
				.where(Post.id == comment.post_id)
				.values(comment_count=func.greatest(Post.comment_count - 1, 0))
			)
			await self.db.commit()

	async def follow_user(self, *, follower_id: uuid.UUID, following_id: uuid.UUID) -> None:
		if follower_id == following_id:
			raise BadRequestException("Không thể follow chính mình")

		target = await self.db.scalar(select(User).where(User.id == following_id))
		if target is None:
			raise NotFoundException("User không tồn tại")

		self.db.add(Follow(follower_id=follower_id, following_id=following_id))
		try:
			actor = await self.db.scalar(select(User).where(User.id == follower_id))
			await NotificationService(self.db).create_notification(
				user_id=following_id,
				notification_type="follow",
				data={
					"actor_id": str(follower_id),
					"actor_username": actor.username if actor else None,
				},
			)
			await self.db.commit()
		except IntegrityError as exc:
			await self.db.rollback()
			raise ConflictException("Bạn đã follow user này") from exc

	async def unfollow_user(self, *, follower_id: uuid.UUID, following_id: uuid.UUID) -> None:
		result = await self.db.execute(
			delete(Follow).where(
				Follow.follower_id == follower_id,
				Follow.following_id == following_id,
			)
		)
		if result.rowcount == 0:
			raise NotFoundException("Bạn chưa follow user này")
		await self.db.commit()

	async def list_followers(
		self,
		*,
		user_id: uuid.UUID,
		target_user_id: uuid.UUID,
		page: int,
		page_size: int,
	) -> FollowListResponse:
		return await self._list_follow_edges(
			mode="followers",
			target_user_id=target_user_id,
			page=page,
			page_size=page_size,
		)

	async def list_following(
		self,
		*,
		user_id: uuid.UUID,
		target_user_id: uuid.UUID,
		page: int,
		page_size: int,
	) -> FollowListResponse:
		return await self._list_follow_edges(
			mode="following",
			target_user_id=target_user_id,
			page=page,
			page_size=page_size,
		)

	async def _list_follow_edges(
		self,
		*,
		mode: str,
		target_user_id: uuid.UUID,
		page: int,
		page_size: int,
	) -> FollowListResponse:
		offset = (page - 1) * page_size
		if mode == "followers":
			count_stmt = select(func.count()).select_from(Follow).where(Follow.following_id == target_user_id)
			stmt = (
				select(User)
				.join(Follow, Follow.follower_id == User.id)
				.where(Follow.following_id == target_user_id)
				.order_by(Follow.created_at.desc())
			)
		else:
			count_stmt = select(func.count()).select_from(Follow).where(Follow.follower_id == target_user_id)
			stmt = (
				select(User)
				.join(Follow, Follow.following_id == User.id)
				.where(Follow.follower_id == target_user_id)
				.order_by(Follow.created_at.desc())
			)

		total = await self.db.scalar(count_stmt)
		rows = await self.db.scalars(stmt.offset(offset).limit(page_size))
		users = rows.all()

		items = [UserPublicResponse.model_validate(user) for user in users]
		return FollowListResponse.create(
			items=items,
			total=int(total or 0),
			page=page,
			page_size=page_size,
		)

	async def _get_following_ids(self, *, user_id: uuid.UUID) -> set[uuid.UUID]:
		rows = await self.db.execute(
			select(Follow.following_id).where(Follow.follower_id == user_id)
		)
		return {row[0] for row in rows.all()}

	async def _get_liked_post_ids(self, *, user_id: uuid.UUID, post_ids: list[uuid.UUID]) -> set[uuid.UUID]:
		if not post_ids:
			return set()
		rows = await self.db.execute(
			select(Like.post_id).where(Like.user_id == user_id, Like.post_id.in_(post_ids))
		)
		return {row[0] for row in rows.all()}

	async def _get_post(self, post_id: uuid.UUID) -> Post | None:
		return await self.db.scalar(
			select(Post)
			.options(
				selectinload(Post.user),
				selectinload(Post.submission).selectinload(Submission.user_quest).selectinload(UserQuest.quest),
				selectinload(Post.quest),
			)
			.where(Post.id == post_id)
		)

	async def _get_post_by_submission(self, *, user_id: uuid.UUID, submission_id: uuid.UUID) -> Post | None:
		return await self.db.scalar(
			select(Post)
			.options(
				selectinload(Post.user),
				selectinload(Post.submission).selectinload(Submission.user_quest).selectinload(UserQuest.quest),
				selectinload(Post.quest),
			)
			.where(Post.user_id == user_id, Post.submission_id == submission_id)
		)

	@staticmethod
	def _to_post_response(post: Post, *, liked_by_me: bool) -> PostResponse:
		submission_image_url = post.image_url or (post.submission.image_url if post.submission else None)

		quest_info = None
		
		# PRIORITY 1: Load quest data linked via physical submission
		if post.submission and post.submission.user_quest and post.submission.user_quest.quest:
			q = post.submission.user_quest.quest
			quest_info = PostQuestInfo(
				id=q.id,
				title=q.title,
				description=q.description,
				xp_reward=q.xp_reward,
			)
		# PRIORITY 2: Fallback to direct post-to-quest linkage for "Tag only" free posts
		elif post.quest:
			q = post.quest
			quest_info = PostQuestInfo(
				id=q.id,
				title=q.title,
				description=q.description,
				xp_reward=q.xp_reward,
			)

		return PostResponse(
			id=post.id,
			submission_id=post.submission_id,
			submission_image_url=submission_image_url,
			caption=post.caption,
			quest=quest_info,
			user=UserPublicResponse.model_validate(post.user),
			like_count=post.like_count,
			comment_count=post.comment_count,
			liked_by_me=liked_by_me,
			created_at=post.created_at,
		)

	@staticmethod
	def _to_comment_response(comment: Comment) -> CommentResponse:
		content = "" if comment.is_deleted else comment.content
		return CommentResponse(
			id=comment.id,
			post_id=comment.post_id,
			parent_id=comment.parent_id,
			user=UserPublicResponse.model_validate(comment.user),
			content=content,
			is_deleted=comment.is_deleted,
			created_at=comment.created_at,
		)
