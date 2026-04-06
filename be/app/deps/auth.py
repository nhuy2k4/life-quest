import uuid
from dataclasses import dataclass

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CredentialsException, ForbiddenException
from app.core.security import decode_access_token, is_token_blacklisted
from app.deps.db import get_db
from app.models.user import User

# HTTP Bearer scheme — dán access token trực tiếp trong Swagger Authorize
bearer_scheme = HTTPBearer(auto_error=True)
optional_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    """
    User context inject vào route handlers.
    Không chứa sensitive data (password_hash, v.v.)
    """

    id: uuid.UUID
    role: str
    onboarding_completed: bool
    is_banned: bool


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """
    Dependency xác thực JWT và trả về CurrentUser context.

    Flow:
    1. Decode JWT → lấy user_id, role, jti
    2. Check jti trong Redis blacklist (logout/revoke)
    3. Query user từ DB (không dùng thông tin trong token nữa — SSoT)
    4. Check is_banned → 403
    """
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise CredentialsException("Token đã hết hạn")
    except jwt.InvalidTokenError:
        raise CredentialsException("Token không hợp lệ")

    user_id: str | None = payload.get("sub")
    jti: str | None = payload.get("jti")

    if not user_id or not jti:
        raise CredentialsException("Token thiếu thông tin cần thiết")

    # Kiểm tra token có bị blacklist không (sau logout)
    if await is_token_blacklisted(jti):
        raise CredentialsException("Token đã bị thu hồi")

    # Query user từ DB — đảm bảo role/ban status luôn mới nhất
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise CredentialsException("User không tồn tại")

    if user.is_banned:
        raise ForbiddenException("Tài khoản đã bị khóa")

    return CurrentUser(
        id=user.id,
        role=user.role,
        onboarding_completed=user.onboarding_completed,
        is_banned=user.is_banned,
    )


async def require_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Dependency bảo vệ admin endpoints.
    Bắt buộc dùng trên tất cả /admin/* routers.
    """
    if current_user.role != "admin":
        raise ForbiddenException("Chỉ admin mới có quyền truy cập")
    return current_user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser | None:
    """
    Optional auth — trả None nếu không có token.
    Dùng cho endpoints công khai có behaviour khác khi đăng nhập.
    """
    if credentials is None:
        return None

    token = credentials.credentials

    try:
        return await get_current_user(
            credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
            db=db,
        )
    except Exception:
        return None
