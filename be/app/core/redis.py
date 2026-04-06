from typing import Any, Optional
import redis.asyncio as aioredis

from app.core.config import settings

# ── Singleton Redis client ────────────────────────────────────────────────────
_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """Trả về Redis client singleton, khởi tạo nếu chưa có."""
    global _redis_client
    if _redis_client is None:
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
