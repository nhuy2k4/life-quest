from __future__ import annotations

import asyncio
import logging
import uuid

from app.core.database import AsyncSessionLocal
from app.models.audit import AiDetectionLog
from app.models.enums import SubmissionStatus, UserQuestStatus
from app.models.recommendation import RecommendationLog
from app.models.quest_instance import QuestInstance
from app.models.social import Post
from sqlalchemy.dialects.postgresql import insert
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
			from sqlalchemy import select
			from app.models.social import Post

			# Check if this submission is linked to a post with an event_id
			post_event_id = await session.scalar(
				select(Post.event_id)
				.where(Post.submission_id == submission.id)
			)

			if submission.user_quest.quest.location_required and not post_event_id:
				match = await poi_matcher.match_poi(db=session, lat=submission.lat, lng=submission.lng)
				if match is not None:
					submission.poi_id = match.poi.id
					submission.poi_distance_m = match.distance_m
					if submission.user_quest.poi_id is None:
						submission.user_quest.poi_id = match.poi.id
					# Create quest instance mapping if it doesn't exist yet.
					await session.execute(
						insert(QuestInstance)
						.values(
							quest_id=submission.user_quest.quest_id,
							user_id=submission.user_quest.user_id,
							poi_id=match.poi.id,
						)
						.on_conflict_do_nothing()
					)

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
			submission.user_quest.status = UserQuestStatus.APPROVED

			base_xp = submission.user_quest.quest.xp_reward
			poi_validated = decision.ai_metadata.get("poi_validated", False)
			total_potential_xp = int(base_xp * 1.5) if poi_validated else base_xp

			xp_granted = max(0, total_potential_xp - submission.user_quest.consolation_xp)

			if xp_granted > 0:
				await submission_service.xp_service.grant_for_submission(
					user_id=submission.user_quest.user_id,
					submission_id=submission.id,
					amount=xp_granted,
				)
			await NotificationService(session).create_notification(
				user_id=submission.user_quest.user_id,
				notification_type="quest_complete",
				data={
					"submission_id": str(submission.id),
					"quest_id": str(submission.user_quest.quest_id),
					"xp_granted": xp_granted,
					"poi_validated": poi_validated,
				},
			)

			# ── Update user streak ────────────────────────────────────────────
			try:
				from datetime import datetime, timezone, timedelta
				from app.models.submission import Submission
				from app.models.user_quest import UserQuest
				from app.models.user import User
				from sqlalchemy import select

				user_id_val = submission.user_quest.user_id
				user_obj = await session.scalar(select(User).where(User.id == user_id_val))
				if user_obj:
					# Check the date of the previous approved submission (excluding this one)
					stmt = (
						select(Submission.created_at)
						.join(UserQuest, Submission.user_quest_id == UserQuest.id)
						.where(
							UserQuest.user_id == user_id_val,
							Submission.status == SubmissionStatus.APPROVED,
							Submission.id != submission.id
						)
						.order_by(Submission.created_at.desc())
						.limit(1)
					)
					last_approved_time = await session.scalar(stmt)
					
					now_time = datetime.now(timezone.utc)
					vn_tz_val = timezone(timedelta(hours=7))
					current_date_val = now_time.astimezone(vn_tz_val).date()

					if last_approved_time:
						if last_approved_time.tzinfo is None:
							last_approved_time = last_approved_time.replace(tzinfo=timezone.utc)
						last_approved_date_val = last_approved_time.astimezone(vn_tz_val).date()

						if current_date_val == last_approved_date_val:
							# Same day, do nothing
							pass
						elif current_date_val == last_approved_date_val + timedelta(days=1):
							# Yesterday, increment!
							user_obj.streak_days += 1
						else:
							# Overdue, streak broke, reset to 1
							user_obj.streak_days = 1
					else:
						# First approved quest!
						user_obj.streak_days = 1
			except Exception:
				logger.exception("Failed to update streak for user %s", submission.user_quest.user_id)

			# ── Auto-unlock badges ────────────────────────────────────────────
			try:
				from app.services.gamification.badge_service import BadgeService
				badge_service = BadgeService(session)
				await session.flush()  # Ensure DB sees the updated UserQuest status before counting
				newly_awarded = await badge_service.evaluate_and_award_badges(
					user_id=submission.user_quest.user_id,
				)
				for awarded_badge in newly_awarded:
					await NotificationService(session).create_notification(
						user_id=submission.user_quest.user_id,
						notification_type="badge_unlocked",
						data={
							"badge_id": str(awarded_badge.id),
							"badge_name": awarded_badge.name,
							"badge_rarity": awarded_badge.rarity,
							"badge_icon_url": awarded_badge.icon_url,
						},
					)
			except Exception:
				logger.exception("Badge evaluation failed for user %s", submission.user_quest.user_id)

			session.add(
				RecommendationLog(
					user_id=submission.user_quest.user_id,
					quest_id=submission.user_quest.quest_id,
					event="completed",
					score=6.0,
					rank=0,
					request_id=uuid.uuid4(),
					algorithm_version="rule_based_mvp_v1",
				)
			)
		elif decision.decision == ApprovalDecisionType.REJECT or decision.decision == ApprovalDecisionType.MANUAL_REVIEW:
			import math
			from app.models.enums import XpSource
			submission.status = SubmissionStatus.REJECTED
			# Thay vì khóa cứng REJECTED, đưa về NOT_STARTED để user được phép Try Again/Làm lại luôn
			submission.user_quest.status = UserQuestStatus.REJECTED
			# Keep event_id linked even if the submission is rejected so it shows as Not eligible in Event Details
			# await session.execute(
			# 	Post.__table__.update()
			# 	.where(Post.submission_id == submission.id)
			# 	.values(event_id=None)
			# )

			consolation_awarded = 0
			if decision.decision == ApprovalDecisionType.REJECT:
				base_xp = submission.user_quest.quest.xp_reward
				current_retry = submission.retry_count
				# 10% for first fail (retry_count=0), halving each time
				consolation_awarded = math.ceil((base_xp * 0.1) * (0.5 ** current_retry))
				if consolation_awarded > 0:
					submission.user_quest.consolation_xp += consolation_awarded
					await repository.create_xp_transaction(
						user_id=submission.user_quest.user_id,
						submission_id=submission.id,
						amount=consolation_awarded,
						source=XpSource.CONSOLATION,
					)
					user = await repository.get_user_by_id(submission.user_quest.user_id)
					if user:
						user.xp += consolation_awarded
						level = await repository.get_level_for_xp(user.xp)
						if level and user.level_id != level.id:
							user.level_id = level.id

			await NotificationService(session).create_notification(
				user_id=submission.user_quest.user_id,
				notification_type="quest_rejected",
				data={
					"submission_id": str(submission.id),
					"quest_id": str(submission.user_quest.quest_id),
					"reason": submission.ai_metadata.get("reason") if submission.ai_metadata else None,
					"retry_count": submission.retry_count,
					"consolation_xp": consolation_awarded,
				},
			)
		else:
			# Dự phòng fallback nếu có trạng thái lạ
			submission.status = SubmissionStatus.PENDING

		await repository.commit()
