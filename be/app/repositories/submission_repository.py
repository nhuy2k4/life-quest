import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import XpSource
from app.models.quest import Quest
from app.models.submission import Submission
from app.models.user import User
from app.models.user_quest import UserQuest
from app.models.xp_transaction import XpTransaction
from app.schemas.submission import AdminSubmissionFilterStatus


class SubmissionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_submission_by_id(self, submission_id: uuid.UUID) -> Submission | None:
        stmt = (
            select(Submission)
            .where(Submission.id == submission_id)
            .options(
                selectinload(Submission.user_quest).selectinload(UserQuest.quest),
            )
        )
        return await self.db.scalar(stmt)

    async def get_submission_for_update(self, submission_id: uuid.UUID) -> Submission | None:
        stmt = (
            select(Submission)
            .where(Submission.id == submission_id)
            .options(
                selectinload(Submission.user_quest).selectinload(UserQuest.quest),
            )
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_submissions(
        self,
        *,
        status: AdminSubmissionFilterStatus | None,
        offset: int,
        limit: int,
    ) -> tuple[list[Submission], int]:
        base = select(Submission)
        total_base = select(func.count()).select_from(Submission)

        if status:
            base = base.where(Submission.status == status)
            total_base = total_base.where(Submission.status == status)

        stmt = (
            base.options(selectinload(Submission.user_quest).selectinload(UserQuest.quest))
            .order_by(Submission.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        total = await self.db.scalar(total_base)
        return list(result.scalars().all()), int(total or 0)

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.db.scalar(select(User).where(User.id == user_id))

    async def get_xp_transaction_by_submission_id(self, submission_id: uuid.UUID) -> XpTransaction | None:
        stmt = select(XpTransaction).where(XpTransaction.submission_id == submission_id)
        return await self.db.scalar(stmt)

    async def create_xp_transaction(
        self,
        *,
        user_id: uuid.UUID,
        submission_id: uuid.UUID,
        amount: int,
        source: XpSource = XpSource.QUEST_APPROVED,
    ) -> XpTransaction:
        item = XpTransaction(
            user_id=user_id,
            submission_id=submission_id,
            amount=amount,
            source=source,
        )
        self.db.add(item)
        await self.db.flush()
        return item

    async def commit(self) -> None:
        await self.db.commit()
