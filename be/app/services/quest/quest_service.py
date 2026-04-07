from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BadRequestException, ConflictException, ForbiddenException, NotFoundException
from app.models.enums import SubmissionStatus, UserQuestStatus
from app.models.user_quest import STARTED_STATUSES
from app.repositories.quest_repository import QuestRepository
from app.schemas.quest import (
	QuestDetailResponse,
	QuestListItemResponse,
	StartQuestResponse,
	SubmitQuestRequest,
	SubmitQuestResponse,
)


class QuestService:
	"""Quest business logic with strict state-transition checks."""

	def __init__(self, repository: QuestRepository) -> None:
		self.repository = repository

	async def list_quests(self, *, user_id: UUID, page: int, page_size: int) -> tuple[list[QuestListItemResponse], int]:
		offset = (page - 1) * page_size
		quests, total = await self.repository.list_active_quests(offset=offset, limit=page_size)

		items: list[QuestListItemResponse] = []
		for quest in quests:
			user_quest = await self.repository.get_user_quest(user_id=user_id, quest_id=quest.id)
			items.append(
				QuestListItemResponse(
					id=quest.id,
					title=quest.title,
					description=quest.description,
					xp_reward=quest.xp_reward,
					difficulty=quest.difficulty,
					time_limit_hours=quest.time_limit_hours,
					location_required=quest.location_required,
					is_active=quest.is_active,
					user_status=user_quest.normalized_status if user_quest else UserQuestStatus.NOT_STARTED,
				)
			)

		return items, total

	async def get_quest_detail(self, *, user_id: UUID, quest_id: UUID) -> QuestDetailResponse:
		quest = await self.repository.get_quest_by_id(quest_id)
		if quest is None or not quest.is_active:
			raise NotFoundException("Quest không tồn tại")

		user_quest = await self.repository.get_user_quest(user_id=user_id, quest_id=quest_id)
		return QuestDetailResponse(
			id=quest.id,
			title=quest.title,
			description=quest.description,
			xp_reward=quest.xp_reward,
			difficulty=quest.difficulty,
			approval_rate=quest.approval_rate,
			time_limit_hours=quest.time_limit_hours,
			location_required=quest.location_required,
			is_active=quest.is_active,
			user_status=user_quest.normalized_status if user_quest else UserQuestStatus.NOT_STARTED,
			started_at=user_quest.started_at if user_quest else None,
			expires_at=user_quest.expires_at if user_quest else None,
		)

	async def start_quest(self, *, user_id: UUID, onboarding_completed: bool, quest_id: UUID) -> StartQuestResponse:
		if not onboarding_completed:
			raise ForbiddenException("Bạn cần hoàn tất onboarding trước khi bắt đầu quest")

		quest = await self.repository.get_quest_by_id(quest_id)
		if quest is None or not quest.is_active:
			raise NotFoundException("Quest không tồn tại")

		now = datetime.now(timezone.utc)
		user_quest = await self.repository.get_user_quest(user_id=user_id, quest_id=quest_id)

		if user_quest is not None:
			if user_quest.normalized_status in {
				UserQuestStatus.STARTED,
				UserQuestStatus.SUBMITTED,
				UserQuestStatus.APPROVED,
				UserQuestStatus.REJECTED,
			}:
				raise ConflictException("Quest đã được bắt đầu trước đó")

			user_quest.status = UserQuestStatus.STARTED
			user_quest.started_at = now
			user_quest.expires_at = self._compute_expires_at(now=now, time_limit_hours=quest.time_limit_hours)
			await self.repository.commit()
			return StartQuestResponse(
				user_quest_id=user_quest.id,
				quest_id=quest.id,
				status=UserQuestStatus.STARTED,
				started_at=user_quest.started_at,
				expires_at=user_quest.expires_at,
			)

		try:
			created = await self.repository.create_user_quest(
				user_id=user_id,
				quest_id=quest.id,
				status=UserQuestStatus.STARTED,
				started_at=now,
				expires_at=self._compute_expires_at(now=now, time_limit_hours=quest.time_limit_hours),
			)
			await self.repository.commit()
		except IntegrityError as exc:
			raise ConflictException("Quest đã được bắt đầu trước đó") from exc

		return StartQuestResponse(
			user_quest_id=created.id,
			quest_id=quest.id,
			status=UserQuestStatus.STARTED,
			started_at=created.started_at,
			expires_at=created.expires_at,
		)

	async def submit_quest(
		self,
		*,
		user_id: UUID,
		onboarding_completed: bool,
		quest_id: UUID,
		payload: SubmitQuestRequest,
	) -> SubmitQuestResponse:
		if not onboarding_completed:
			raise ForbiddenException("Bạn cần hoàn tất onboarding trước khi nộp quest")

		quest = await self.repository.get_quest_by_id(quest_id)
		if quest is None or not quest.is_active:
			raise NotFoundException("Quest không tồn tại")

		user_quest = await self.repository.get_user_quest_for_update(user_id=user_id, quest_id=quest_id)
		if user_quest is None:
			raise BadRequestException("Bạn cần bắt đầu quest trước khi nộp")

		if user_quest.normalized_status not in STARTED_STATUSES:
			raise ConflictException("Quest không ở trạng thái có thể nộp")

		now = datetime.now(timezone.utc)
		expires_at = self._to_utc_aware(user_quest.expires_at)
		if expires_at is not None and expires_at <= now:
			user_quest.status = UserQuestStatus.REJECTED
			await self.repository.commit()
			raise BadRequestException("Quest đã hết hạn nộp")

		existing_submission = await self.repository.get_submission_by_user_quest_id(user_quest.id)
		if existing_submission is not None:
			raise ConflictException("Quest đã được nộp trước đó")

		try:
			submission = await self.repository.create_submission(
				user_quest_id=user_quest.id,
				image_url=payload.image_url,
				cloudinary_public_id=payload.cloudinary_public_id,
				file_hash=payload.file_hash,
			)
			user_quest.status = UserQuestStatus.SUBMITTED
			await self.repository.commit()
		except IntegrityError as exc:
			raise ConflictException("Quest đã được nộp trước đó") from exc

		return SubmitQuestResponse(
			submission_id=submission.id,
			user_quest_id=user_quest.id,
			status=UserQuestStatus.SUBMITTED,
			submission_status=SubmissionStatus.PENDING,
			submitted_at=submission.created_at,
		)

	@staticmethod
	def _compute_expires_at(*, now: datetime, time_limit_hours: int | None) -> datetime | None:
		if time_limit_hours is None:
			return None
		return now + timedelta(hours=time_limit_hours)

	@staticmethod
	def _to_utc_aware(value: datetime | None) -> datetime | None:
		"""Normalize DB datetime values to UTC-aware for safe comparisons."""
		if value is None:
			return None
		if value.tzinfo is None:
			return value.replace(tzinfo=timezone.utc)
		return value
