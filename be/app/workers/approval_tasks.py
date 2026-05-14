from __future__ import annotations

import asyncio
import logging
import uuid

from app.core.database import AsyncSessionLocal
from app.models.audit import AiDetectionLog
from app.models.enums import SubmissionStatus, UserQuestStatus
from app.repositories.submission_repository import SubmissionRepository
from app.services.ai.ai_approval_service import ApprovalDecisionType
from app.services.notification.notification_service import NotificationService
from app.services.poi import poi_matcher
from app.services.pipeline.approval_pipeline import run_approval_pipeline
from app.services.submission.submission_service import SubmissionService
from app.workers.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(name="approval.process_submission_ai")
def process_submission_ai(submission_id: str) -> None:
	asyncio.run(_process_submission_ai(submission_id))


async def _process_submission_ai(submission_id: str) -> None:
	try:
		submission_uuid = uuid.UUID(submission_id)
	except ValueError:
		logger.warning("Invalid submission_id for AI approval: %s", submission_id)
		return

	async with AsyncSessionLocal() as session:
		repository = SubmissionRepository(session)
		submission_service = SubmissionService(repository)

		submission = await repository.get_submission_for_update(submission_uuid)
		if submission is None or submission.user_quest is None or submission.user_quest.quest is None:
			logger.warning("Submission not found for AI approval: %s", submission_id)
			return

		if submission.status != SubmissionStatus.PENDING:
			return

		submission.status = SubmissionStatus.PROCESSING
		await repository.commit()

		if submission.lat is not None and submission.lng is not None:
			match = await poi_matcher.match_poi(db=session, lat=submission.lat, lng=submission.lng)
			if match is not None:
				submission.poi_id = match.poi.id
				submission.poi_distance_m = match.distance_m

		decision = run_approval_pipeline(submission)

		submission.ai_score = decision.ai_score
		submission.cheat_flags = decision.cheat_flags
		submission.is_suspicious = decision.is_suspicious
		submission.vision_labels = decision.vision_labels
		submission.vision_raw = decision.vision_raw
		submission.ai_metadata = decision.ai_metadata

		confidence_stats = {
			"max_score": decision.vision_max_score,
			"label_count": len(decision.vision_labels),
		}
		session.add(
			AiDetectionLog(
				submission_id=submission.id,
				labels=decision.vision_labels,
				raw_response=decision.vision_raw,
				confidence_stats=confidence_stats,
			)
		)

		if decision.decision == ApprovalDecisionType.APPROVE:
			submission.status = SubmissionStatus.APPROVED
			submission.rejection_reason = None
			submission.user_quest.status = UserQuestStatus.APPROVED
			await submission_service.xp_service.grant_for_submission(
				user_id=submission.user_quest.user_id,
				submission_id=submission.id,
				amount=submission.user_quest.quest.xp_reward,
			)
			await NotificationService(session).create_notification(
				user_id=submission.user_quest.user_id,
				notification_type="quest_complete",
				data={
					"submission_id": str(submission.id),
					"quest_id": str(submission.user_quest.quest_id),
					"xp_granted": submission.user_quest.quest.xp_reward,
				},
			)
		elif decision.decision == ApprovalDecisionType.REJECT or decision.decision == ApprovalDecisionType.MANUAL_REVIEW:
			submission.status = SubmissionStatus.REJECTED
			# Thay vì khóa cứng REJECTED, đưa về NOT_STARTED để user được phép Try Again/Làm lại luôn
			submission.user_quest.status = UserQuestStatus.REJECTED
			await NotificationService(session).create_notification(
				user_id=submission.user_quest.user_id,
				notification_type="quest_rejected",
				data={
					"submission_id": str(submission.id),
					"quest_id": str(submission.user_quest.quest_id),
					"reason": submission.ai_metadata.get("reason") if submission.ai_metadata else None,
					"retry_count": submission.retry_count,
				},
			)
		else:
			# Dự phòng fallback nếu có trạng thái lạ
			submission.status = SubmissionStatus.PENDING

		await repository.commit()
