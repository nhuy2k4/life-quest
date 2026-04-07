from __future__ import annotations

from typing import Any

from app.core.redis import redis_exists, redis_set

ONLINE_KEY_PREFIX = "user:online"
ONLINE_TTL_SECONDS = 60


def build_user_online_key(user_id: str) -> str:
    """Build Redis key used to track a user's online presence."""
    return f"{ONLINE_KEY_PREFIX}:{user_id}"


def _extract_user_id(user_ctx: Any) -> str | None:
    """Extract user id from request.state.user (object or dict)."""
    if user_ctx is None:
        return None

    if isinstance(user_ctx, dict):
        candidate = user_ctx.get("id") or user_ctx.get("user_id") or user_ctx.get("sub")
        return str(candidate) if candidate is not None else None

    candidate = getattr(user_ctx, "id", None) or getattr(user_ctx, "user_id", None)
    return str(candidate) if candidate is not None else None


async def mark_user_online(user_id: str) -> None:
    """Set online marker with short TTL for near real-time presence."""
    await redis_set(build_user_online_key(user_id), "1", ttl=ONLINE_TTL_SECONDS)


async def mark_user_online_from_state(user: Any | None = None, user_id: Any | None = None) -> None:
    """Best-effort helper to mark online from request.state payloads."""
    resolved_user_id = str(user_id) if user_id is not None else _extract_user_id(user)
    if not resolved_user_id:
        return

    await mark_user_online(resolved_user_id)


async def is_user_online(user_id: str) -> bool:
    """Return True if the user has an active online key in Redis."""
    return await redis_exists(build_user_online_key(user_id))
