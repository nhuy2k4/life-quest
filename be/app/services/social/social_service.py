import uuid

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, ConflictException, ForbiddenException, NotFoundException
from app.models.recommendation import RecommendationLog
from app.models.event import Event, EventQuest
from app.models.social import Comment, Follow, Like, Post
from app.models.quest_instance import QuestInstance
from app.models.poi import Poi
from app.models.submission import Submission
from app.models.user import User
from app.models.user_quest import UserQuest
from app.models.quest import Quest
from app.models.enums import EventStatus, SubmissionStatus
from app.schemas.common import PaginatedResponse
from app.schemas.social import (
	CommentCreateRequest,
	CommentListResponse,
	CommentResponse,
	FeedResponse,
	FollowListResponse,
	PostCreateRequest,
	PostQuestInfo,
	PostEventInfo,
	PostResponse,
)
from app.schemas.user import UserPublicResponse
from app.services.notification.notification_service import NotificationService


class SocialService:
	def __init__(self, db: AsyncSession) -> None:
		self.db = db

	async def get_feed(self, *, user_id: uuid.UUID, page: int, page_size: int, scope: str = "all") -> FeedResponse:
		offset = (page - 1) * page_size

		base = select(Post)
		total_base = select(func.count()).select_from(Post)
		if scope == "following":
			following_subquery = select(Follow.following_id).where(Follow.follower_id == user_id)
			base = base.where(Post.user_id.in_(following_subquery))
			total_base = total_base.where(Post.user_id.in_(following_subquery))

		total = await self.db.scalar(total_base)
		rows = await self.db.scalars(
			base
			.options(
				selectinload(Post.user),
				selectinload(Post.submission).selectinload(Submission.poi),
				selectinload(Post.submission).selectinload(Submission.user_quest).selectinload(UserQuest.quest),
				selectinload(Post.quest),
				selectinload(Post.poi),
				selectinload(Post.event),
			)
			.order_by(Post.created_at.desc())
			.offset(offset)
			.limit(page_size)
		)
		posts = rows.all()


		liked_post_ids = await self._get_liked_post_ids(user_id=user_id, post_ids=[post.id for post in posts])
		following_ids = await self._get_following_ids(user_id=user_id)
		counts_by_post = await self._get_post_counts(post_ids=[post.id for post in posts])
		items = [
			self._to_post_response(
				post,
				liked_by_me=post.id in liked_post_ids,
				followed_by_me=post.user_id in following_ids,
				counts=counts_by_post.get(post.id),
			)
			for post in posts
		]

		return FeedResponse.create(
			items=items,
			total=int(total or 0),
			page=page,
			page_size=page_size,
		)

	async def search_posts(self, *, user_id: uuid.UUID, query: str, page: int, page_size: int) -> FeedResponse:
		offset = (page - 1) * page_size
		term = f"%{query.strip()}%"
		filter_expr = or_(
			Post.caption.ilike(term),
			User.username.ilike(term),
		)
		base = select(Post).join(User, Post.user_id == User.id).where(filter_expr)
		total_base = select(func.count()).select_from(Post).join(User, Post.user_id == User.id).where(filter_expr)

		total = await self.db.scalar(total_base)
		rows = await self.db.scalars(
			base
			.options(
				selectinload(Post.user),
				selectinload(Post.submission).selectinload(Submission.poi),
				selectinload(Post.submission).selectinload(Submission.user_quest).selectinload(UserQuest.quest),
				selectinload(Post.quest),
				selectinload(Post.poi),
				selectinload(Post.event),
			)
			.order_by(Post.created_at.desc())
			.offset(offset)
			.limit(page_size)
		)
		posts = rows.all()

		liked_post_ids = await self._get_liked_post_ids(user_id=user_id, post_ids=[post.id for post in posts])
		following_ids = await self._get_following_ids(user_id=user_id)
		counts_by_post = await self._get_post_counts(post_ids=[post.id for post in posts])
		items = [
			self._to_post_response(
				post,
				liked_by_me=post.id in liked_post_ids,
				followed_by_me=post.user_id in following_ids,
				counts=counts_by_post.get(post.id),
			)
			for post in posts
		]
		return FeedResponse.create(items=items, total=int(total or 0), page=page, page_size=page_size)

	async def create_post(self, *, user_id: uuid.UUID, payload: PostCreateRequest) -> PostResponse:
		quest_id: uuid.UUID | None = None
		event_id: uuid.UUID | None = None
		quest: Quest | None = None

		if payload.submission_id:
			existing_post = await self._get_post_by_submission(
				user_id=user_id,
				submission_id=payload.submission_id,
			)
			if existing_post is not None:
				return self._to_post_response(existing_post, liked_by_me=False)

			submission = await self.db.scalar(
				select(Submission)
				.options(selectinload(Submission.user_quest))
				.join(UserQuest, Submission.user_quest_id == UserQuest.id)
				.where(Submission.id == payload.submission_id, UserQuest.user_id == user_id)
			)
			if submission is None:
				raise NotFoundException("Submission không tồn tại hoặc không thuộc về bạn")
			quest_id = submission.user_quest.quest_id if submission.user_quest else None
			event_id = (
				await self._get_active_event_id_for_quest(quest_id=quest_id)
				if submission.status == SubmissionStatus.APPROVED
				else None
			)
			post = Post(
				user_id=user_id,
				submission_id=payload.submission_id,
				quest_id=quest_id,
				event_id=event_id,
				caption=payload.caption,
				location_name=payload.location_name,
				poi_id=payload.poi_id,
			)
		else:
			if not payload.image_url:
				raise BadRequestException("image_url lÃ  báº¯t buá»™c khi táº¡o post khÃ´ng cÃ³ submission")

			if payload.quest_id:
				quest = await self.db.scalar(select(Quest).where(Quest.id == payload.quest_id, Quest.is_active.is_(True)))
				if quest is None:
					raise NotFoundException("Quest khÃ´ng tá»“n táº¡i hoáº·c Ä‘Ã£ bá»‹ táº¯t")

			effective_poi_id = payload.poi_id
			if quest is not None and not quest.location_required:
				effective_poi_id = None

			if effective_poi_id:
				poi = await self.db.scalar(select(Poi).where(Poi.id == effective_poi_id, Poi.is_active.is_(True)))
				if poi is None:
					raise NotFoundException("POI khÃ´ng tá»“n táº¡i hoáº·c Ä‘Ã£ bá»‹ táº¯t")

			quest_id = payload.quest_id if quest else None
			post = Post(
				user_id=user_id, 
				image_url=payload.image_url, 
				caption=payload.caption,
				location_name=payload.location_name,
				quest_id=quest_id,
				event_id=None,
				poi_id=effective_poi_id,
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

		if payload.quest_id and quest is not None and quest.location_required and payload.poi_id:
			await self.db.execute(
				insert(QuestInstance)
				.values(
					quest_id=payload.quest_id,
					user_id=user_id,
					poi_id=payload.poi_id,
				)
				.on_conflict_do_nothing()
			)
			await self.db.commit()

		try:
			from app.services.gamification.badge_service import BadgeService
			badge_service = BadgeService(self.db)
			await badge_service.evaluate_and_award_badges(user_id=user_id)
			await self.db.commit()
		except Exception:
			await self.db.rollback()

		stored = await self._get_post(post.id)
		if stored is None:
			raise NotFoundException("Post không tồn tại")
		counts = (await self._get_post_counts(post_ids=[stored.id])).get(stored.id)
		return self._to_post_response(stored, liked_by_me=False, counts=counts)

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
		await self._log_post_interaction(user_id=user_id, post=post, event="post_liked")
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

		try:
			from app.services.gamification.badge_service import BadgeService
			badge_service = BadgeService(self.db)
			await self.db.flush()
			await badge_service.evaluate_and_award_badges(user_id=post.user_id)
		except Exception:
			await self.db.rollback()
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
		await self._log_post_interaction(user_id=user_id, post=post, event="post_commented")
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

		try:
			from app.services.gamification.badge_service import BadgeService
			badge_service = BadgeService(self.db)
			await self.db.flush()
			await badge_service.evaluate_and_award_badges(user_id=user_id)
		except Exception:
			await self.db.rollback()
		await self.db.commit()

		stored = await self._get_post(post_id)
		if stored is None:
			raise NotFoundException("Post không tồn tại")
		counts = (await self._get_post_counts(post_ids=[stored.id])).get(stored.id)
		return self._to_post_response(stored, liked_by_me=False, counts=counts)

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

		existing = await self.db.scalar(
			select(Follow).where(
				Follow.follower_id == follower_id,
				Follow.following_id == following_id,
			)
		)
		if existing is not None:
			return

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

	async def _get_post_counts(self, *, post_ids: list[uuid.UUID]) -> dict[uuid.UUID, tuple[int, int]]:
		if not post_ids:
			return {}
		like_rows = await self.db.execute(
			select(Like.post_id, func.count().label("count"))
			.where(Like.post_id.in_(post_ids))
			.group_by(Like.post_id)
		)
		comment_rows = await self.db.execute(
			select(Comment.post_id, func.count().label("count"))
			.where(Comment.post_id.in_(post_ids), Comment.is_deleted.is_(False))
			.group_by(Comment.post_id)
		)
		counts = {post_id: [0, 0] for post_id in post_ids}
		for post_id, count in like_rows.all():
			counts[post_id][0] = int(count or 0)
		for post_id, count in comment_rows.all():
			counts[post_id][1] = int(count or 0)
		return {post_id: (values[0], values[1]) for post_id, values in counts.items()}

	async def _get_post_quest_id(self, post: Post) -> uuid.UUID | None:
		if post.quest_id is not None:
			return post.quest_id
		if post.submission_id is None:
			return None
		return await self.db.scalar(
			select(UserQuest.quest_id)
			.join(Submission, Submission.user_quest_id == UserQuest.id)
			.where(Submission.id == post.submission_id)
		)

	async def _log_post_interaction(self, *, user_id: uuid.UUID, post: Post, event: str) -> None:
		quest_id = await self._get_post_quest_id(post)
		score = 3.0 if event == "post_commented" else 1.0
		self.db.add(
			RecommendationLog(
				user_id=user_id,
				quest_id=quest_id,
				post_id=post.id,
				event=event,
				score=score,
				rank=0,
				request_id=uuid.uuid4(),
				algorithm_version="social_interaction_v1",
			)
		)

	async def _get_post(self, post_id: uuid.UUID) -> Post | None:
		return await self.db.scalar(
			select(Post)
			.options(
				selectinload(Post.user),
				selectinload(Post.submission).selectinload(Submission.poi),
				selectinload(Post.submission).selectinload(Submission.user_quest).selectinload(UserQuest.quest),
				selectinload(Post.quest),
				selectinload(Post.poi),
				selectinload(Post.event),
			)
			.where(Post.id == post_id)
		)

	async def _get_post_by_submission(self, *, user_id: uuid.UUID, submission_id: uuid.UUID) -> Post | None:
		return await self.db.scalar(
			select(Post)
			.options(
				selectinload(Post.user),
				selectinload(Post.submission).selectinload(Submission.poi),
				selectinload(Post.submission).selectinload(Submission.user_quest).selectinload(UserQuest.quest),
				selectinload(Post.quest),
				selectinload(Post.poi),
				selectinload(Post.event),
			)
			.where(Post.user_id == user_id, Post.submission_id == submission_id)
		)

	async def _get_active_event_id_for_quest(self, *, quest_id: uuid.UUID | None) -> uuid.UUID | None:
		if quest_id is None:
			return None
		now = func.now()
		event_id = await self.db.scalar(
			select(Event.id)
			.join(EventQuest, EventQuest.event_id == Event.id)
			.where(
				EventQuest.quest_id == quest_id,
				Event.status == EventStatus.ACTIVE,
				Event.start_at <= now,
				Event.end_at >= now,
			)
			.order_by(Event.start_at.desc())
			.limit(1)
		)
		return event_id

	@staticmethod
	def _to_post_response(
		post: Post,
		*,
		liked_by_me: bool,
		followed_by_me: bool = False,
		counts: tuple[int, int] | None = None,
	) -> PostResponse:
		submission_image_url = post.image_url or (post.submission.image_url if post.submission else None)
		submission_poi_name = post.submission.poi.name if post.submission and post.submission.poi else None
		submission_poi_id = post.submission.poi_id if post.submission else None
		post_poi_name = post.poi.name if post.poi else None
		post_poi_id = post.poi_id
		user_quest_poi_id = (
			post.submission.user_quest.poi_id
			if post.submission and post.submission.user_quest
			else None
		)

		quest_info = None
		event_info = None
		
		# PRIORITY 1: Load quest data linked via physical submission
		if post.submission and post.submission.user_quest and post.submission.user_quest.quest:
			q = post.submission.user_quest.quest
			quest_info = PostQuestInfo(
				id=q.id,
				poi_id=submission_poi_id or user_quest_poi_id or post_poi_id,
				title=q.title,
				description=q.description,
				xp_reward=q.xp_reward,
				poi_name=submission_poi_name or post_poi_name,
			)
		# PRIORITY 2: Fallback to direct post-to-quest linkage for "Tag only" free posts
		elif post.quest:
			q = post.quest
			quest_info = PostQuestInfo(
				id=q.id,
				poi_id=post_poi_id,
				title=q.title,
				description=q.description,
				xp_reward=q.xp_reward,
				poi_name=post_poi_name or submission_poi_name,
			)

		if post.event:
			event_info = PostEventInfo(
				id=post.event.id,
				title=post.event.title,
			)

		like_count, comment_count = counts if counts is not None else (post.like_count, post.comment_count)
		return PostResponse(
			id=post.id,
			submission_id=post.submission_id,
			submission_image_url=submission_image_url,
			caption=post.caption,
			location_name=post.location_name or post_poi_name,
			quest=quest_info,
			event=event_info,
			user=UserPublicResponse.model_validate(post.user),
			like_count=like_count,
			comment_count=comment_count,
			liked_by_me=liked_by_me,
			followed_by_me=followed_by_me,
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
