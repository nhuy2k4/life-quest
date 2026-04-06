from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import RateLimitException
from app.core.redis import redis_incr

# ── Rate limit config ─────────────────────────────────────────────────────────
RATE_LIMITS: dict[str, tuple[int, int]] = {
    # path_prefix: (max_requests, window_seconds)
    "/api/v1/auth/login": (5, 60),       # 5 lần/phút — anti brute force
    "/api/v1/auth/register": (3, 60),    # 3 lần/phút — anti spam
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Redis sliding window rate limiting theo IP.

    Key format: rate_limit:{path}:{ip}
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Tìm rule áp dụng
        limit_config = None
        for prefix, config in RATE_LIMITS.items():
            if path.startswith(prefix):
                limit_config = config
                break

        if limit_config is not None:
            max_requests, window_seconds = limit_config
            client_ip = self._get_client_ip(request)
            redis_key = f"rate_limit:{path}:{client_ip}"

            count = await redis_incr(redis_key, ttl=window_seconds)
            if count > max_requests:
                raise RateLimitException(
                    f"Quá nhiều request. Vui lòng thử lại sau {window_seconds} giây."
                )

        return await call_next(request)

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Lấy IP thật, handle trường hợp đứng sau proxy/load balancer."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"
