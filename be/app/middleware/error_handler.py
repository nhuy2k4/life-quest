import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger("lifequest")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global exception handler — bắt tất cả lỗi chưa được handle.

    - Development: trả stack trace để debug
    - Production (DEBUG=False): ẩn stack trace, log ra server
    """

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.exception(
                "Unhandled exception | %s %s | req_id=%s",
                request.method,
                request.url.path,
                request_id,
            )

            if settings.DEBUG:
                # Dev: trả đủ thông tin để debug
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": str(exc),
                        "error_code": "INTERNAL_SERVER_ERROR",
                        "request_id": request_id,
                    },
                )
            else:
                # Production: ẩn internal detail
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": "Lỗi hệ thống. Vui lòng thử lại sau.",
                        "error_code": "INTERNAL_SERVER_ERROR",
                    },
                )
