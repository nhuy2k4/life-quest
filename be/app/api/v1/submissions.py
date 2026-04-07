from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import CurrentUser, get_current_user, require_admin
from app.deps.db import get_db
from app.repositories.submission_repository import SubmissionRepository
from app.schemas.submission import (
	AdminSubmissionActionResponse,
	AdminSubmissionFilterStatus,
	AdminSubmissionListResponse,
	RejectSubmissionRequest,
	SubmissionResponse,
)
from app.services.submission.submission_service import SubmissionService

router = APIRouter(tags=["Submissions"])


def get_submission_service(db: AsyncSession = Depends(get_db)) -> SubmissionService:
	return SubmissionService(SubmissionRepository(db))


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
async def get_submission_detail(
	submission_id: UUID,
	current_user: CurrentUser = Depends(get_current_user),
	service: SubmissionService = Depends(get_submission_service),
) -> SubmissionResponse:
	return await service.get_submission_for_user(submission_id=submission_id, user_id=current_user.id)


@router.get("/admin/submissions", response_model=AdminSubmissionListResponse)
async def list_submissions_for_admin(
	status: AdminSubmissionFilterStatus | None = Query(default=None),
	page: int = Query(default=1, ge=1),
	page_size: int = Query(default=20, ge=1, le=100),
	_admin: CurrentUser = Depends(require_admin),
	service: SubmissionService = Depends(get_submission_service),
) -> AdminSubmissionListResponse:
	return await service.list_submissions_for_admin(
		status=status,
		page=page,
		page_size=page_size,
	)


@router.patch("/admin/submissions/{submission_id}/approve", response_model=AdminSubmissionActionResponse)
async def approve_submission(
	submission_id: UUID,
	_admin: CurrentUser = Depends(require_admin),
	service: SubmissionService = Depends(get_submission_service),
) -> AdminSubmissionActionResponse:
	return await service.approve_submission(submission_id=submission_id)


@router.patch("/admin/submissions/{submission_id}/reject", response_model=AdminSubmissionActionResponse)
async def reject_submission(
	submission_id: UUID,
	payload: RejectSubmissionRequest,
	_admin: CurrentUser = Depends(require_admin),
	service: SubmissionService = Depends(get_submission_service),
) -> AdminSubmissionActionResponse:
	return await service.reject_submission(submission_id=submission_id, reason=payload.reason)
