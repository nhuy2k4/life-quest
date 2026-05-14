import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.xp_transaction import XpTransaction
from app.schemas.common import PaginatedResponse
from app.schemas.gamification import XpHistoryItem, XpHistoryResponse


class XpHistoryService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_xp_history(self, *, user_id: uuid.UUID, page: int, page_size: int) -> XpHistoryResponse:
        offset = (page - 1) * page_size

        total_stmt = select(func.count()).select_from(XpTransaction).where(XpTransaction.user_id == user_id)
        total = await self.db.scalar(total_stmt)

        rows_stmt = (
            select(XpTransaction)
            .where(XpTransaction.user_id == user_id)
            .order_by(XpTransaction.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = await self.db.scalars(rows_stmt)

        items = [XpHistoryItem.model_validate(row) for row in rows.all()]
        return XpHistoryResponse.create(items=items, total=int(total or 0), page=page, page_size=page_size)
