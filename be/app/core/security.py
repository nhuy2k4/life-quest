import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import bcrypt
import jwt

from app.core.config import settings
from app.core.redis import redis_delete, redis_exists, redis_set


# ── Password hashing ──────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash mật khẩu với bcrypt (cost factor 12)."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Xác minh mật khẩu với hash đã lưu."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── Token creation ────────────────────────────────────────────────────────────

def create_access_token(
    user_id: UUID,
    role: str,
    expires_delta: timedelta | None = None,
) -> tuple[str, str]:
    """
    Tạo JWT access token.

    Returns:
        (token_string, jti) — jti dùng để blacklist khi logout
    """
    jti = secrets.token_hex(16)
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "jti": jti,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token, jti


def create_refresh_token() -> tuple[str, str]:
    """
    Tạo opaque refresh token (32 bytes random hex).

    Returns:
        (raw_token, token_hash) — lưu hash vào DB, trả raw cho client
    """
    raw = secrets.token_hex(32)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, token_hash


def hash_refresh_token(raw: str) -> str:
    """Hash refresh token để so sánh với DB."""
    return hashlib.sha256(raw.encode()).hexdigest()


# ── Token decoding ────────────────────────────────────────────────────────────

def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode JWT, trả payload dict.

    Raises:
        jwt.ExpiredSignatureError: token hết hạn
        jwt.InvalidTokenError: token không hợp lệ
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


# ── Token blacklist (Redis) ───────────────────────────────────────────────────

BLACKLIST_PREFIX = "token_blacklist:"


async def blacklist_token(jti: str, expire_at: datetime) -> None:
    """
    Thêm jti vào Redis blacklist.
    TTL = thời gian còn lại đến khi token hết hạn.
    """
    now = datetime.now(timezone.utc)
    ttl_seconds = max(int((expire_at - now).total_seconds()), 1)
    await redis_set(f"{BLACKLIST_PREFIX}{jti}", "1", ttl=ttl_seconds)


async def is_token_blacklisted(jti: str) -> bool:
    """Kiểm tra jti có trong blacklist không."""
    return await redis_exists(f"{BLACKLIST_PREFIX}{jti}")
