from datetime import datetime
import uuid

from pydantic import BaseModel

from app.models.enums import XpSource
from app.schemas.common import PaginatedResponse


class XpHistoryItem(BaseModel):
    id: uuid.UUID
    amount: int
    source: XpSource
    submission_id: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class XpHistoryResponse(PaginatedResponse[XpHistoryItem]):
    pass
