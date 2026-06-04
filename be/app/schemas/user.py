import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserMeResponse(BaseModel):
    """Profile đầy đủ — dùng sau register và GET /users/me."""

    id: uuid.UUID
    username: str
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
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
    avatar_url: str | None = None
    level_id: int
    xp: int
    streak_days: int

    model_config = {"from_attributes": True}


class UserProfileStatsResponse(BaseModel):
    posts: int = 0
    streak: int = 0
    quests_completed: int = 0
    followers: int = 0
    following: int = 0


class UserPublicProfileResponse(BaseModel):
    id: uuid.UUID
    username: str
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    level_id: int
    xp: int
    streak_days: int
    is_following: bool = False
    is_self: bool = False
    stats: UserProfileStatsResponse


class UserPublicProfileDataResponse(BaseModel):
    data: UserPublicProfileResponse


class UpdateProfileRequest(BaseModel):
    """PATCH /users/me — chỉ update các trường được phép."""

    username: Optional[str] = None
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[EmailStr] = None


class UserMeDataResponse(BaseModel):
    """Wrapper response cho endpoint trả về dạng {"data": ...}."""

    data: UserMeResponse
