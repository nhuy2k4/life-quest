from typing import Any, Optional
import os
import time
import redis.asyncio as aioredis

from app.core.config import settings

# ── Singleton Redis client ────────────────────────────────────────────────────
_redis_client: Optional[aioredis.Redis] = None


class _InMemoryRedis:
    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float | None]] = {}

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self._store[key] = (value, time.time() + ttl)

    async def set(self, key: str, value: str) -> None:
        self._store[key] = (value, None)

    async def get(self, key: str) -> Optional[str]:
        item = self._store.get(key)
        if item is None:
            return None
        value, expires_at = item
        if expires_at is not None and expires_at <= time.time():
            self._store.pop(key, None)
            return None
        return value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def exists(self, key: str) -> int:
        value = await self.get(key)
        return 1 if value is not None else 0

    async def incr(self, key: str) -> int:
        value = await self.get(key)
        next_value = int(value or 0) + 1
        self._store[key] = (str(next_value), None)
        return next_value

    async def expire(self, key: str, ttl: int) -> None:
        value = await self.get(key)
        if value is None:
            return
        self._store[key] = (value, time.time() + ttl)

    async def aclose(self) -> None:
        self._store.clear()


async def get_redis_client() -> aioredis.Redis:
    """Trả về Redis client singleton, khởi tạo nếu chưa có."""
    global _redis_client
    if _redis_client is None:
        if os.getenv("PYTEST_CURRENT_TEST") is not None:
            _redis_client = _InMemoryRedis()  # type: ignore[assignment]
            return _redis_client
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Đóng kết nối Redis khi shutdown."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


# ── Helper functions ──────────────────────────────────────────────────────────

async def redis_set(key: str, value: str, ttl: Optional[int] = None) -> None:
    """Set key-value, tuỳ chọn TTL tính bằng giây."""
    client = await get_redis_client()
    if ttl:
        await client.setex(key, ttl, value)
    else:
        await client.set(key, value)


async def redis_get(key: str) -> Optional[str]:
    """Get value theo key, trả None nếu không tìm thấy."""
    client = await get_redis_client()
    return await client.get(key)


async def redis_delete(key: str) -> None:
    """Xoá key khỏi Redis."""
    client = await get_redis_client()
    await client.delete(key)


async def redis_exists(key: str) -> bool:
    """Kiểm tra key có tồn tại không."""
    client = await get_redis_client()
    return bool(await client.exists(key))


async def redis_incr(key: str, ttl: Optional[int] = None) -> int:
    """Tăng counter, dùng cho rate limiting. Trả về giá trị mới."""
    client = await get_redis_client()
    value = await client.incr(key)
    if value == 1 and ttl:
        # Set TTL chỉ lần đầu để sliding window chính xác
        await client.expire(key, ttl)
    return value
