import uuid

from app.core.exceptions import ConflictException, NotFoundException, ForbiddenException
from app.models.enums import SubmissionStatus, UserQuestStatus
from app.models.recommendation import RecommendationLog
from app.models.social import Post
from app.repositories.submission_repository import SubmissionRepository
from app.schemas.submission import (
	AdminSubmissionActionResponse,
	AdminSubmissionFilterStatus,
	AdminSubmissionItem,
	AdminSubmissionListResponse,
	SubmissionResponse,
)
from app.services.gamification.xp_service import XpService
from app.services.notification.notification_service import NotificationService


class SubmissionService:
	def __init__(self, repository: SubmissionRepository) -> None:
		self.repository = repository
		self.xp_service = XpService(repository)

	async def get_submission_for_user(self, *, submission_id: uuid.UUID, user_id: uuid.UUID) -> SubmissionResponse:
		submission = await self.repository.get_submission_by_id(submission_id)
		if submission is None or submission.user_quest is None:
			raise NotFoundException("Submission không tồn tại")

		if submission.user_quest.user_id != user_id:
			raise ForbiddenException("Không có quyền truy cập submission này")

		return SubmissionResponse.model_validate(submission)

	async def list_submissions_for_admin(
		self,
		*,
		status: AdminSubmissionFilterStatus | None,
		page: int,
		page_size: int,
	) -> AdminSubmissionListResponse:
		offset = (page - 1) * page_size
		rows, total = await self.repository.list_submissions(status=status, offset=offset, limit=page_size)

		items: list[AdminSubmissionItem] = []
		for item in rows:
			if item.user_quest is None:
				continue
			items.append(
				AdminSubmissionItem(
					id=item.id,
					user_quest_id=item.user_quest_id,
					quest_id=item.user_quest.quest_id,
					user_id=item.user_quest.user_id,
					image_url=item.image_url,
					status=item.status,
					is_suspicious=item.is_suspicious,
					retry_count=item.retry_count,
					created_at=item.created_at,
				)
			)

		return AdminSubmissionListResponse(items=items, total=total, page=page, page_size=page_size)

	async def approve_submission(self, *, submission_id: uuid.UUID) -> AdminSubmissionActionResponse:
		submission = await self.repository.get_submission_for_update(submission_id)
		if submission is None or submission.user_quest is None or submission.user_quest.quest is None:
			raise NotFoundException("Submission không tồn tại")

		if submission.status == SubmissionStatus.APPROVED:
			raise ConflictException("Submission đã được duyệt")

		if submission.status == SubmissionStatus.REJECTED:
			raise ConflictException("Submission đã bị từ chối")

		submission.status = SubmissionStatus.APPROVED
		submission.user_quest.status = UserQuestStatus.APPROVED

		xp_granted = await self.xp_service.grant_for_submission(
			user_id=submission.user_quest.user_id,
			submission_id=submission.id,
			amount=submission.user_quest.quest.xp_reward,
		)
		await NotificationService(self.repository.db).create_notification(
			user_id=submission.user_quest.user_id,
			notification_type="quest_complete",
			data={
				"submission_id": str(submission.id),
				"quest_id": str(submission.user_quest.quest_id),
				"xp_granted": xp_granted,
			},
		)
		self.repository.db.add(
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

		await self.repository.commit()
		return AdminSubmissionActionResponse(
			submission_id=submission.id,
			status=SubmissionStatus.APPROVED,
			user_quest_status=UserQuestStatus.APPROVED,
			xp_granted=xp_granted,
		)

	async def reject_submission(self, *, submission_id: uuid.UUID, reason: str) -> AdminSubmissionActionResponse:
		submission = await self.repository.get_submission_for_update(submission_id)
		if submission is None or submission.user_quest is None:
			raise NotFoundException("Submission không tồn tại")

		if submission.status == SubmissionStatus.APPROVED:
			raise ConflictException("Submission đã được duyệt")

		submission.status = SubmissionStatus.REJECTED
		submission.user_quest.status = UserQuestStatus.REJECTED
		# Keep event_id linked even if the submission is rejected so it shows as Not eligible in Event Details
		# await self.repository.db.execute(
		# 	Post.__table__.update()
		# 	.where(Post.submission_id == submission.id)
		# 	.values(event_id=None)
		# )
		await NotificationService(self.repository.db).create_notification(
			user_id=submission.user_quest.user_id,
			notification_type="quest_rejected",
			data={
				"submission_id": str(submission.id),
				"quest_id": str(submission.user_quest.quest_id),
				"reason": reason.strip(),
				"retry_count": submission.retry_count,
			},
		)

		await self.repository.commit()
		return AdminSubmissionActionResponse(
			submission_id=submission.id,
			status=SubmissionStatus.REJECTED,
			user_quest_status=UserQuestStatus.REJECTED,
			xp_granted=0,
		)
