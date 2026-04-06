import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserMeResponse(BaseModel):
    """Profile đầy đủ — dùng sau register và GET /users/me."""

    id: uuid.UUID
    username: str
    email: str
    role: str
    level_id: int
    xp: int
    streak_days: int
    trust_score: float
    onboarding_completed: bool
    is_banned: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserPublicResponse(BaseModel):
    """Profile công khai — hiển thị trên feed/social."""

    id: uuid.UUID
    username: str
    level_id: int
    xp: int
    streak_days: int

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    """PATCH /users/me — chỉ update các trường được phép."""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
