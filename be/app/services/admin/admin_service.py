import uuid
from datetime import datetime, timezone

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.security import hash_password
from app.models.audit import AuditLog
from app.models.enums import QuestDifficulty, SubmissionStatus, XpSource
from app.models.auth import Level
from app.models.badge import Badge
from app.models.event import Event
from app.models.poi import Poi
from app.models.quest import Quest
from app.models.quest import Category as QuestCategoryModel
from app.models.social import Comment, Post
from app.models.submission import Submission
from app.models.user import User
from app.models.user_quest import UserQuest
from app.models.xp_transaction import XpTransaction
from app.schemas.admin import (
	AdminCategoryItem,
	AdminDashboardStatsResponse,
	AdminEventParticipationStat,
	AdminPostInteractionStat,
	AdminQuestItem,
	AdminQuestCompletionStat,
	AdminQuestListResponse,
	AdminQuestUpdateRequest,
	AdminUserItem,
	AdminUserListResponse,
	AdminUserXpAdjustRequest,
	AdminUserXpAdjustResponse,
	AdminPoiItem,
	AdminPoiListResponse,
	AdminPoiCreateRequest,
	AdminPoiUpdateRequest,
	AdminPostActionResponse,
	AdminBadgeItem,
	AdminBadgeListResponse,
	AdminBadgeCreateRequest,
	AdminBadgeUpdateRequest,
	AdminBadgeConditionType,
	AdminBadgeConditionTypesResponse,
	BADGE_CATEGORIES,
	BADGE_CONDITION_TYPES,
	BADGE_RARITIES,
	AdminPostItem,
	AdminPostListResponse,
	AdminCommentItem,
	AdminCommentListResponse,
)
from app.schemas.user import UserPublicResponse




class AdminService:
	def __init__(self, db: AsyncSession) -> None:
		self.db = db

	async def list_users(self, *, page: int, page_size: int) -> AdminUserListResponse:
		offset = (page - 1) * page_size
		total = await self.db.scalar(select(func.count()).select_from(User).where(User.role != "admin"))
		rows = await self.db.scalars(
			select(User)
			.where(User.role != "admin")
			.order_by(User.created_at.desc())
			.offset(offset)
			.limit(page_size)
		)
		items = [AdminUserItem.model_validate(user) for user in rows.all()]
		return AdminUserListResponse.create(items=items, total=int(total or 0), page=page, page_size=page_size)

	async def set_user_ban(self, *, user_id: uuid.UUID, is_banned: bool) -> None:
		user = await self.db.scalar(select(User).where(User.id == user_id))
		if user is None:
			raise NotFoundException("User không tồn tại")
		user.is_banned = is_banned
		self.db.add(AuditLog(action="user_ban", target_type="user", target_id=user.id))
		await self.db.commit()

	async def update_user(self, *, user_id: uuid.UUID, payload) -> None:
		user = await self.db.scalar(select(User).where(User.id == user_id))
		if user is None:
			raise NotFoundException("User không tồn tại")
		data = payload.model_dump(exclude_unset=True)
		audit_meta: dict = {}
		for field, val in data.items():
			if field == "password":
				user.password_hash = hash_password(val)
				audit_meta["password_changed"] = True
			else:
				setattr(user, field, val)
				audit_meta[field] = val
		self.db.add(AuditLog(action="user_update", target_type="user", target_id=user.id, meta=audit_meta))
		await self.db.commit()

	async def adjust_user_xp(
		self,
		*,
		user_id: uuid.UUID,
		payload: AdminUserXpAdjustRequest,
	) -> AdminUserXpAdjustResponse:
		user = await self.db.scalar(select(User).where(User.id == user_id))
		if user is None:
			raise NotFoundException("User không tồn tại")
		if payload.amount == 0:
			raise BadRequestException("Số XP điều chỉnh phải khác 0")

		transaction = XpTransaction(
			user_id=user.id,
			submission_id=None,
			amount=payload.amount,
			source=XpSource.ADMIN_ADJUST,
		)
		self.db.add(transaction)
		user.xp = max(user.xp + payload.amount, 0)
		level = await self.db.scalar(
			select(Level)
			.where(Level.required_xp <= user.xp)
			.order_by(Level.required_xp.desc())
			.limit(1)
		)
		if level is not None and user.level_id != level.id:
			user.level_id = level.id
		self.db.add(AuditLog(
			action="xp_adjust",
			target_type="user",
			target_id=user.id,
			meta={"amount": payload.amount, "reason": payload.reason},
		))
		await self.db.commit()
		return AdminUserXpAdjustResponse(user_id=user.id, amount=payload.amount, new_xp=user.xp)

	async def list_quests(self, *, page: int, page_size: int) -> AdminQuestListResponse:
		offset = (page - 1) * page_size
		total = await self.db.scalar(select(func.count()).select_from(Quest))
		rows = await self.db.scalars(
			select(Quest)
			.options(selectinload(Quest.categories))
			.order_by(Quest.created_at.desc())
			.offset(offset)
			.limit(page_size)
		)
		items = [
			AdminQuestItem(
				id=quest.id,
				title=quest.title,
				image_url=quest.image_url,
				description=quest.description,
				difficulty=quest.difficulty.value,
				xp_reward=quest.xp_reward,
				approval_rate=quest.approval_rate,
				time_limit_hours=quest.time_limit_hours,
				categories=[
					AdminCategoryItem(id=c.id, name=c.name, slug=c.slug)
					for c in quest.categories
				],
				is_active=quest.is_active,
				created_at=quest.created_at,
			)
			for quest in rows.all()
		]
		return AdminQuestListResponse.create(items=items, total=int(total or 0), page=page, page_size=page_size)

	async def update_quest(self, *, quest_id: uuid.UUID, payload: AdminQuestUpdateRequest) -> None:
		quest = await self.db.scalar(select(Quest).where(Quest.id == quest_id))
		if quest is None:
			raise NotFoundException("Quest không tồn tại")

		data = payload.model_dump(exclude_unset=True)
		if "difficulty" in data and data["difficulty"] is not None:
			try:
				data["difficulty"] = QuestDifficulty(data["difficulty"])
			except ValueError as exc:
				raise BadRequestException("Quest difficulty khong hop le") from exc
		for field, value in data.items():
			setattr(quest, field, value)

		self.db.add(AuditLog(action="quest_update", target_type="quest", target_id=quest.id, meta=data))
		await self.db.commit()

	async def get_dashboard_stats(self) -> AdminDashboardStatsResponse:
		now = datetime.now(timezone.utc)
		day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
		month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

		async def quest_completion_stats(since: datetime) -> list[AdminQuestCompletionStat]:
			rows = await self.db.execute(
				select(
					Quest.id,
					Quest.title,
					func.count(Submission.id).label("completed_count"),
				)
				.join(UserQuest, UserQuest.quest_id == Quest.id)
				.join(Submission, Submission.user_quest_id == UserQuest.id)
				.where(
					Submission.status == SubmissionStatus.APPROVED,
					Submission.created_at >= since,
				)
				.group_by(Quest.id, Quest.title)
				.order_by(func.count(Submission.id).desc(), Quest.title.asc())
				.limit(10)
			)
			return [
				AdminQuestCompletionStat(
					quest_id=row.id,
					title=row.title,
					completed_count=int(row.completed_count or 0),
				)
				for row in rows.all()
			]

		post_rows = await self.db.execute(
			select(
				Post.id,
				Post.caption,
				User.username,
				Post.like_count,
				Post.comment_count,
				(Post.like_count + Post.comment_count).label("interaction_count"),
				Post.created_at,
			)
			.join(User, Post.user_id == User.id)
			.order_by((Post.like_count + Post.comment_count).desc(), Post.created_at.desc())
			.limit(10)
		)
		top_posts = [
			AdminPostInteractionStat(
				post_id=row.id,
				caption=row.caption,
				author=row.username,
				like_count=int(row.like_count or 0),
				comment_count=int(row.comment_count or 0),
				interaction_count=int(row.interaction_count or 0),
				created_at=row.created_at,
			)
			for row in post_rows.all()
		]

		event_rows = await self.db.execute(
			select(
				Event.id,
				Event.title,
				Event.status,
				Event.start_at,
				Event.end_at,
				func.count(func.distinct(Post.user_id)).label("participant_count"),
			)
			.outerjoin(Post, Post.event_id == Event.id)
			.group_by(Event.id, Event.title, Event.status, Event.start_at, Event.end_at)
			.order_by(func.count(func.distinct(Post.user_id)).desc(), Event.start_at.desc())
			.limit(10)
		)
		top_events = [
			AdminEventParticipationStat(
				event_id=row.id,
				title=row.title,
				status=row.status.value if hasattr(row.status, "value") else str(row.status),
				participant_count=int(row.participant_count or 0),
				start_at=row.start_at,
				end_at=row.end_at,
			)
			for row in event_rows.all()
		]

		return AdminDashboardStatsResponse(
			quests_completed_today=await quest_completion_stats(day_start),
			quests_completed_this_month=await quest_completion_stats(month_start),
			top_interaction_posts=top_posts,
			top_participation_events=top_events,
		)

	async def delete_post(self, *, post_id: uuid.UUID) -> None:
		post = await self.db.scalar(
			select(Post).options(selectinload(Post.comments)).where(Post.id == post_id)
		)
		if post is None:
			raise NotFoundException("Post không tồn tại")

		await self.db.delete(post)
		self.db.add(AuditLog(action="post_delete", target_type="post", target_id=post.id))
		await self.db.commit()

	async def delete_comment(self, *, comment_id: uuid.UUID) -> None:
		comment = await self.db.scalar(select(Comment).where(Comment.id == comment_id))
		if comment is None:
			raise NotFoundException("Comment không tồn tại")

		await self.db.delete(comment)
		self.db.add(AuditLog(action="comment_delete", target_type="comment", target_id=comment.id))
		await self.db.commit()

	async def list_posts(
		self,
		*,
		page: int,
		page_size: int,
		query: str | None = None,
	) -> AdminPostListResponse:
		offset = (page - 1) * page_size
		base = select(Post)
		total_base = select(func.count()).select_from(Post)

		if query:
			term = f"%{query.strip()}%"
			filter_expr = or_(
				Post.caption.ilike(term),
				Post.location_name.ilike(term),
				User.username.ilike(term),
			)
			base = base.join(User, Post.user_id == User.id).where(filter_expr)
			total_base = total_base.join(User, Post.user_id == User.id).where(filter_expr)

		total = await self.db.scalar(total_base)
		rows = await self.db.scalars(
			base
			.options(
				selectinload(Post.user),
				selectinload(Post.quest),
				selectinload(Post.submission),
			)
			.order_by(Post.created_at.desc())
			.offset(offset)
			.limit(page_size)
		)
		posts = rows.all()

		items = []
		for post in posts:
			media_url = post.image_url
			if media_url is None and post.submission is not None:
				media_url = post.submission.image_url
			items.append(
				AdminPostItem(
					id=post.id,
					user=UserPublicResponse.model_validate(post.user),
					caption=post.caption,
					media_url=media_url,
					location_name=post.location_name,
					quest_id=post.quest_id,
					quest_title=post.quest.title if post.quest else None,
					submission_id=post.submission_id,
					like_count=post.like_count,
					comment_count=post.comment_count,
					created_at=post.created_at,
				)
			)

		return AdminPostListResponse.create(
			items=items,
			total=int(total or 0),
			page=page,
			page_size=page_size,
		)

	async def list_post_comments(
		self,
		*,
		post_id: uuid.UUID,
		page: int,
		page_size: int,
	) -> AdminCommentListResponse:
		offset = (page - 1) * page_size
		total = await self.db.scalar(
			select(func.count()).select_from(Comment).where(Comment.post_id == post_id)
		)
		rows = await self.db.scalars(
			select(Comment)
			.options(selectinload(Comment.user))
			.where(Comment.post_id == post_id)
			.order_by(Comment.created_at.desc())
			.offset(offset)
			.limit(page_size)
		)
		items = [
			AdminCommentItem(
				id=comment.id,
				post_id=comment.post_id,
				user=UserPublicResponse.model_validate(comment.user),
				content=comment.content,
				is_deleted=comment.is_deleted,
				created_at=comment.created_at,
			)
			for comment in rows.all()
		]
		return AdminCommentListResponse.create(
			items=items,
			total=int(total or 0),
			page=page,
			page_size=page_size,
		)

	# Badges

	async def list_badges(self, *, page: int, page_size: int) -> AdminBadgeListResponse:
		offset = (page - 1) * page_size
		total = await self.db.scalar(select(func.count()).select_from(Badge))
		rows = await self.db.scalars(
			select(Badge).order_by(Badge.sort_order.asc(), Badge.created_at.desc()).offset(offset).limit(page_size)
		)
		items = [AdminBadgeItem.model_validate(badge) for badge in rows.all()]
		return AdminBadgeListResponse.create(items=items, total=int(total or 0), page=page, page_size=page_size)

	def list_badge_condition_types(self) -> AdminBadgeConditionTypesResponse:
		labels = {
			"quests_completed": ("Quest completed", "Unlock after completing target quests."),
			"posts_created": ("Posts created", "Unlock after creating target posts."),
			"comments_created": ("Comments created", "Unlock after writing target comments."),
			"likes_received": ("Likes received", "Unlock after receiving target likes."),
			"streak_days": ("Streak days", "Unlock after reaching target streak days."),
			"xp_total": ("Total XP", "Unlock after earning target XP."),
			"level_reached": ("Level reached", "Unlock after reaching target level."),
			"approved_submissions": ("Approved submissions", "Unlock after target approved submissions."),
			"events_participated": ("Events participated", "Unlock after joining target number of events (submitted an approved post)."),
			"event_reward": ("Event Reward (Manual)", "Special badge for event top ranks. Does not auto-unlock. Target is ignored."),
		}
		return AdminBadgeConditionTypesResponse(
			items=[
				AdminBadgeConditionType(value=value, label=labels[value][0], description=labels[value][1])
				for value in sorted(BADGE_CONDITION_TYPES)
			]
		)

	async def create_badge(self, *, payload: AdminBadgeCreateRequest) -> AdminBadgeItem:
		self._validate_badge_payload(
			rarity=payload.rarity,
			category=payload.category,
			condition_type=payload.condition_type,
			icon_url=payload.icon_url,
		)
		existing = await self.db.scalar(select(Badge).where(Badge.name == payload.name))
		if existing is not None:
			raise BadRequestException("Badge name already exists")
		badge = Badge(
			name=payload.name,
			description=payload.description,
			icon_url=payload.icon_url,
			rarity=payload.rarity,
			category=payload.category,
			criteria={"type": payload.condition_type, "target": payload.target},
			is_hidden=payload.is_hidden,
			is_active=payload.is_active,
			sort_order=payload.sort_order,
		)
		self.db.add(badge)
		self.db.add(AuditLog(action="badge_create", target_type="badge", target_id=badge.id))
		await self.db.commit()
		await self.db.refresh(badge)
		return AdminBadgeItem.model_validate(badge)

	async def update_badge(self, *, badge_id: uuid.UUID, payload: AdminBadgeUpdateRequest) -> AdminBadgeItem:
		badge = await self.db.scalar(select(Badge).where(Badge.id == badge_id))
		if badge is None:
			raise NotFoundException("Badge khÃ´ng tá»“n táº¡i")
		data = payload.model_dump(exclude_unset=True)
		rarity = data.get("rarity", badge.rarity)
		category = data.get("category", badge.category)
		condition_type = data.get("condition_type", badge.criteria.get("type"))
		icon_url = data.get("icon_url", badge.icon_url)
		self._validate_badge_payload(
			rarity=rarity,
			category=category,
			condition_type=condition_type,
			icon_url=icon_url,
		)
		if "name" in data and data["name"] != badge.name:
			existing = await self.db.scalar(select(Badge).where(Badge.name == data["name"]))
			if existing is not None:
				raise BadRequestException("Badge name already exists")
		for field in ("name", "description", "icon_url", "rarity", "category", "is_hidden", "is_active", "sort_order"):
			if field in data:
				setattr(badge, field, data[field])
		if "condition_type" in data or "target" in data:
			badge.criteria = {
				"type": condition_type,
				"target": data.get("target", badge.criteria.get("target", badge.criteria.get("count", 1))),
			}
		self.db.add(AuditLog(action="badge_update", target_type="badge", target_id=badge.id))
		await self.db.commit()
		await self.db.refresh(badge)
		return AdminBadgeItem.model_validate(badge)

	async def delete_badge(self, *, badge_id: uuid.UUID) -> None:
		badge = await self.db.scalar(select(Badge).where(Badge.id == badge_id))
		if badge is None:
			raise NotFoundException("Badge khÃ´ng tá»“n táº¡i")
		await self.db.delete(badge)
		self.db.add(AuditLog(action="badge_delete", target_type="badge", target_id=badge.id))
		await self.db.commit()

	@staticmethod
	def _validate_badge_payload(*, rarity: str, category: str, condition_type: str, icon_url: str) -> None:
		if rarity not in BADGE_RARITIES:
			raise BadRequestException("Invalid badge rarity")
		if category not in BADGE_CATEGORIES:
			raise BadRequestException("Invalid badge category")
		if condition_type not in BADGE_CONDITION_TYPES:
			raise BadRequestException("Unsupported badge condition")
		if not (icon_url.startswith("http://") or icon_url.startswith("https://") or len(icon_url) <= 100):
			raise BadRequestException("Invalid badge icon")

	# ── POI ──────────────────────────────────────────────────────────────────

	async def list_pois(
		self, *, page: int, page_size: int, active_only: bool = False
	) -> AdminPoiListResponse:
		query = select(Poi)
		if active_only:
			query = query.where(Poi.is_active == True)  # noqa: E712
		total = await self.db.scalar(
			select(func.count()).select_from(query.subquery())
		)
		offset = (page - 1) * page_size
		rows = await self.db.scalars(
			query.order_by(Poi.created_at.desc()).offset(offset).limit(page_size)
		)
		items = [AdminPoiItem.model_validate(p) for p in rows.all()]
		return AdminPoiListResponse(items=items, total=int(total or 0))

	async def create_poi(self, *, payload: AdminPoiCreateRequest) -> AdminPoiItem:
		import uuid as _uuid
		external_id = payload.external_id or str(_uuid.uuid4())
		poi = Poi(
			name=payload.name,
			poi_type=payload.poi_type,
			latitude=payload.latitude,
			longitude=payload.longitude,
			radius_m=payload.radius_m,
			source=payload.source,
			external_id=external_id,
			external_type=payload.external_type,
			is_active=True,
		)
		self.db.add(poi)
		self.db.add(AuditLog(action="poi_create", target_type="poi", target_id=poi.id))
		await self.db.commit()
		await self.db.refresh(poi)
		return AdminPoiItem.model_validate(poi)

	async def update_poi(self, *, poi_id: uuid.UUID, payload: AdminPoiUpdateRequest) -> AdminPoiItem:
		poi = await self.db.scalar(select(Poi).where(Poi.id == poi_id))
		if poi is None:
			raise NotFoundException("POI không tồn tại")
		for field, val in payload.model_dump(exclude_unset=True).items():
			setattr(poi, field, val)
		self.db.add(AuditLog(action="poi_update", target_type="poi", target_id=poi.id))
		await self.db.commit()
		await self.db.refresh(poi)
		return AdminPoiItem.model_validate(poi)

	async def delete_poi(self, *, poi_id: uuid.UUID) -> None:
		poi = await self.db.scalar(select(Poi).where(Poi.id == poi_id))
		if poi is None:
			raise NotFoundException("POI không tồn tại")
		await self.db.delete(poi)
		self.db.add(AuditLog(action="poi_delete", target_type="poi", target_id=poi.id))
		await self.db.commit()
