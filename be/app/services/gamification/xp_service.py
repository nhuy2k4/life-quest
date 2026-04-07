import uuid

from app.core.exceptions import NotFoundException
from app.models.enums import XpSource
from app.repositories.submission_repository import SubmissionRepository


class XpService:
	"""Grant XP with submission-based idempotency."""

	def __init__(self, repository: SubmissionRepository) -> None:
		self.repository = repository

	async def grant_for_submission(self, *, user_id: uuid.UUID, submission_id: uuid.UUID, amount: int) -> int:
		existing = await self.repository.get_xp_transaction_by_submission_id(submission_id)
		if existing is not None:
			return 0

		user = await self.repository.get_user_by_id(user_id)
		if user is None:
			raise NotFoundException("User không tồn tại")

		await self.repository.create_xp_transaction(
			user_id=user_id,
			submission_id=submission_id,
			amount=amount,
			source=XpSource.QUEST_APPROVED,
		)
		user.xp += amount
		return amount
