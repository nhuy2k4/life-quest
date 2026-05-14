import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import bcrypt
import jwt

from app.core.config import settings
from app.core.redis import redis_exists, redis_set


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
) -> str:
    """
    Tạo JWT access token.

    Returns:
        token_string
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_hex(8),
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


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


async def blacklist_access_token(token: str) -> None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False},
        )
    except jwt.InvalidTokenError:
        return

    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        return

    ttl = int(exp - datetime.now(timezone.utc).timestamp())
    if ttl <= 0:
        return

    await redis_set(f"token_blacklist:{jti}", "1", ttl=ttl)


async def is_token_blacklisted(payload: dict[str, Any]) -> bool:
    jti = payload.get("jti")
    if not jti:
        return False
    return await redis_exists(f"token_blacklist:{jti}")

