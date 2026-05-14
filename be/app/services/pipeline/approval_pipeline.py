from __future__ import annotations

from uuid import UUID

from app.models.submission import Submission
from app.services.ai.ai_approval_service import AIApprovalService, ApprovalDecision


def enqueue_submission_approval(submission_id: UUID) -> None:
	import asyncio
	from app.workers.approval_tasks import _process_submission_ai

	# Run AI background processing directly in current FastAPI event loop without Celery dependency
	asyncio.create_task(_process_submission_ai(str(submission_id)))


def run_approval_pipeline(submission: Submission) -> ApprovalDecision:
	service = AIApprovalService()
	return service.evaluate_submission(submission)
