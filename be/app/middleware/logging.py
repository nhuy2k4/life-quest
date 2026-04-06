import time
import uuid
import logging

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("lifequest")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Log mỗi request/response với format chuẩn:
    method | path | status | latency_ms | user_id | request_id
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        # Gắn request_id vào request state để service layer có thể dùng
        request.state.request_id = request_id

        response = await call_next(request)

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Cố lấy user_id nếu có (không raise lỗi nếu chưa auth)
        user_id = getattr(request.state, "user_id", None)

        logger.info(
            "%s %s %s %.2fms user=%s req_id=%s",
            request.method,
            request.url.path,
            response.status_code,
            latency_ms,
            user_id or "anonymous",
            request_id,
        )

        # Trả request_id về header để client trace
        response.headers["X-Request-ID"] = request_id
        return response
