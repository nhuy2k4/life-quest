from datetime import datetime, timedelta, timezone
from uuid import UUID

import logging

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
from app.services.quest.quest_renderer import render_quest_text
from app.services.pipeline.approval_pipeline import enqueue_submission_approval
from app.services.vision.vision_service import VisionService


logger = logging.getLogger(__name__)

MAX_SUBMISSION_RETRY_COUNT = 3


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
					rendered_text=render_quest_text(quest.template, quest.labels, None),
					labels=quest.labels or [],
					min_confidence=float(quest.min_confidence or 0.5),
					poi_required=quest.poi_required,
					xp_reward=quest.xp_reward,
					is_active=quest.is_active,
					user_status=user_quest.normalized_status if user_quest else UserQuestStatus.NOT_STARTED,
				)
			)

		return items, total

	async def get_quest_detail(self, *, user_id: UUID, quest_id: UUID) -> QuestDetailResponse:
		quest = await self.repository.get_quest_by_id(quest_id)
		if quest is None or not quest.is_active:
			raise NotFoundException("Quest khÃ´ng tá»“n táº¡i")

		user_quest = await self.repository.get_user_quest(user_id=user_id, quest_id=quest_id)
		return QuestDetailResponse(
			id=quest.id,
			rendered_text=render_quest_text(quest.template, quest.labels, None),
			labels=quest.labels or [],
			min_confidence=float(quest.min_confidence or 0.5),
			poi_required=quest.poi_required,
			poi_id=quest.poi_id,
			xp_reward=quest.xp_reward,
			is_active=quest.is_active,
			user_status=user_quest.normalized_status if user_quest else UserQuestStatus.NOT_STARTED,
			started_at=user_quest.started_at if user_quest else None,
			expires_at=user_quest.expires_at if user_quest else None,
		)

	async def start_quest(self, *, user_id: UUID, onboarding_completed: bool, quest_id: UUID) -> StartQuestResponse:
		if not onboarding_completed:
			raise ForbiddenException("Báº¡n cáº§n hoÃ n táº¥t onboarding trÆ°á»›c khi báº¯t Ä‘áº§u quest")

		quest = await self.repository.get_quest_by_id(quest_id)
		if quest is None or not quest.is_active:
			raise NotFoundException("Quest khÃ´ng tá»“n táº¡i")

		now = datetime.now(timezone.utc)
		user_quest = await self.repository.get_user_quest(user_id=user_id, quest_id=quest_id)

		if user_quest is not None:
			if user_quest.normalized_status == UserQuestStatus.STARTED:
				return StartQuestResponse(
					user_quest_id=user_quest.id,
					quest_id=quest.id,
					status=UserQuestStatus.STARTED,
					started_at=user_quest.started_at,
					expires_at=user_quest.expires_at,
				)
			if user_quest.normalized_status in {UserQuestStatus.SUBMITTED, UserQuestStatus.APPROVED}:
				raise ConflictException("Quest Ä‘Ã£ Ä‘Æ°á»£c báº¯t Ä‘áº§u trÆ°á»›c Ä‘Ã³")
			if user_quest.normalized_status == UserQuestStatus.REJECTED:
				existing_submission = await self.repository.get_submission_by_user_quest_id(user_quest.id)
				if existing_submission is not None and existing_submission.retry_count < MAX_SUBMISSION_RETRY_COUNT:
					raise ConflictException("Quest Ä‘ang chá» báº¡n cáº­p nháº­t láº¡i áº£nh")

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
			raise ConflictException("Quest Ä‘Ã£ Ä‘Æ°á»£c báº¯t Ä‘áº§u trÆ°á»›c Ä‘Ã³") from exc

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
			raise ForbiddenException("Báº¡n cáº§n hoÃ n táº¥t onboarding trÆ°á»›c khi ná»™p quest")

		quest = await self.repository.get_quest_by_id(quest_id)
		if quest is None or not quest.is_active:
			raise NotFoundException("Quest khÃ´ng tá»“n táº¡i")

		user_quest = await self.repository.get_user_quest_for_update(user_id=user_id, quest_id=quest_id)
		now = datetime.now(timezone.utc)
		
		existing_submission = await self.repository.get_submission_by_user_quest_id(user_quest.id) if user_quest else None

		if user_quest is None:
			raise BadRequestException("Báº¡n cáº§n báº¯t Ä‘áº§u quest trÆ°á»›c khi ná»™p áº£nh")
		else:
			if (
				existing_submission is not None
				and existing_submission.status != SubmissionStatus.REJECTED
				and existing_submission.file_hash == payload.file_hash
				and user_quest.normalized_status in {UserQuestStatus.SUBMITTED, UserQuestStatus.APPROVED}
			):
				return SubmitQuestResponse(
					submission_id=existing_submission.id,
					user_quest_id=user_quest.id,
					status=user_quest.normalized_status,
					submission_status=existing_submission.status,
					submitted_at=existing_submission.created_at,
					retry_count=existing_submission.retry_count,
					max_retry_count=MAX_SUBMISSION_RETRY_COUNT,
				)

			# Náº¿u nhiá»‡m vá»¥ Ä‘Ã£ á»Ÿ tráº¡ng thÃ¡i Cuá»‘i (Ä‘Ã£ ná»™p/duyá»‡t), cháº·n khÃ´ng cho ná»™p trÃ¹ng
			if user_quest.normalized_status in {UserQuestStatus.SUBMITTED, UserQuestStatus.APPROVED}:
				raise ConflictException("Quest Ä‘Ã£ Ä‘Æ°á»£c ná»™p hoáº·c Ä‘Ã£ hoÃ n thÃ nh trÆ°á»›c Ä‘Ã³")
			
			# Náº¿u nhiá»‡m vá»¥ Ä‘ang treo hoáº·c bá»‹ reject, tá»± Ä‘á»™ng chuyá»ƒn vá» STARTED Ä‘á»ƒ cho phÃ©p ná»™p Ä‘Ã¨/má»›i
			if user_quest.normalized_status not in STARTED_STATUSES:
				if user_quest.normalized_status != UserQuestStatus.REJECTED:
					raise BadRequestException("Tráº¡ng thÃ¡i quest khÃ´ng há»£p lá»‡ Ä‘á»ƒ ná»™p áº£nh")

		expires_at = self._to_utc_aware(user_quest.expires_at)
		if expires_at is not None and expires_at <= now:
			user_quest.status = UserQuestStatus.REJECTED
			await self.repository.commit()
			raise BadRequestException("Quest Ä‘Ã£ háº¿t háº¡n ná»™p")

		if existing_submission is not None:
			if existing_submission.status != SubmissionStatus.REJECTED:
				raise ConflictException("Quest Ä‘Ã£ Ä‘Æ°á»£c ná»™p trÆ°á»›c Ä‘Ã³")
			if existing_submission.retry_count >= MAX_SUBMISSION_RETRY_COUNT:
				raise ConflictException("Báº¡n Ä‘Ã£ háº¿t sá»‘ láº§n cáº­p nháº­t áº£nh cho quest nÃ y")

			submission = await self.repository.update_rejected_submission_for_retry(
				existing_submission,
				image_url=payload.image_url,
				cloudinary_public_id=payload.cloudinary_public_id,
				file_hash=payload.file_hash,
				lat=payload.lat,
				lng=payload.lng,
				location_accuracy_m=payload.location_accuracy_m,
				location_captured_at=payload.location_captured_at,
			)
			user_quest.status = UserQuestStatus.SUBMITTED
			await self.repository.commit()

			try:
				enqueue_submission_approval(submission.id)
			except Exception:
				logger.exception("Failed to enqueue AI approval for submission %s", submission.id)

			return SubmitQuestResponse(
				submission_id=submission.id,
				user_quest_id=user_quest.id,
				status=UserQuestStatus.SUBMITTED,
				submission_status=SubmissionStatus.PENDING,
				submitted_at=submission.created_at,
				retry_count=submission.retry_count,
				max_retry_count=MAX_SUBMISSION_RETRY_COUNT,
			)

		try:
			submission = await self.repository.create_submission(
				user_quest_id=user_quest.id,
				image_url=payload.image_url,
				cloudinary_public_id=payload.cloudinary_public_id,
				file_hash=payload.file_hash,
				lat=payload.lat,
				lng=payload.lng,
				location_accuracy_m=payload.location_accuracy_m,
				location_captured_at=payload.location_captured_at,
			)
			user_quest.status = UserQuestStatus.SUBMITTED
			await self.repository.commit()
		except IntegrityError as exc:
			raise ConflictException("Quest Ä‘Ã£ Ä‘Æ°á»£c ná»™p trÆ°á»›c Ä‘Ã³") from exc

		try:
			enqueue_submission_approval(submission.id)
		except Exception:
			logger.exception("Failed to enqueue AI approval for submission %s", submission.id)

		return SubmitQuestResponse(
			submission_id=submission.id,
			user_quest_id=user_quest.id,
			status=UserQuestStatus.SUBMITTED,
			submission_status=SubmissionStatus.PENDING,
			submitted_at=submission.created_at,
			retry_count=submission.retry_count,
			max_retry_count=MAX_SUBMISSION_RETRY_COUNT,
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

	async def recommend_from_image(
		self,
		*,
		user_id: UUID,
		image_url: str,
		lat: float | None = None,
		lng: float | None = None,
	) -> list[QuestListItemResponse]:
		"""Uses Google Vision to detect what's in the image and recommends quests matching it."""
		try:
			vision_service = VisionService()
			result = vision_service.detect_labels_from_url(image_url)
			detected_labels = {label.description.lower() for label in result.labels}
		except Exception:
			logger.warning("AI label detection failed for recommendations. Defaulting to zero filter.")
			detected_labels = set()

		if not detected_labels:
			return []

		# Fetch reasonable number of active candidates to check (e.g. top 200 recent)
		quests, _ = await self.repository.list_active_quests(offset=0, limit=200)
		matched_items: list[QuestListItemResponse] = []

		for quest in quests:


			# Combine labels from list and key mapping logic exactly like runtime evaluator
			quest_targets = set(quest.labels or [])
			if quest.label_rules:
				quest_targets.update(quest.label_rules.keys())
			
			quest_targets_lower = {t.lower() for t in quest_targets}
			
			# Check if ANY label intersects with detected image labels
			if any(l in detected_labels for l in quest_targets_lower):
				user_quest = await self.repository.get_user_quest(user_id=user_id, quest_id=quest.id)
				# Loáº¡i trá»« cÃ¡c nhiá»‡m vá»¥ Ä‘Ã£ lÃ m rá»“i theo yÃªu cáº§u cá»§a ngÆ°á»i dÃ¹ng
				if user_quest and user_quest.normalized_status in {UserQuestStatus.APPROVED, UserQuestStatus.SUBMITTED}:
					continue
				
				matched_items.append(


					QuestListItemResponse(
						id=quest.id,
						rendered_text=render_quest_text(quest.template, quest.labels, None),
						labels=quest.labels or [],
						min_confidence=float(quest.min_confidence or 0.5),
						poi_required=quest.poi_required,
						xp_reward=quest.xp_reward,
						is_active=quest.is_active,
						user_status=user_quest.normalized_status if user_quest else UserQuestStatus.NOT_STARTED,
					)
				)
		
		return matched_items

