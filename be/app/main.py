import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.redis import close_redis, get_redis_client
from app.middleware.cors import setup_cors
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.online_tracking import OnlineTrackingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("lifequest")


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 LifeQuest API starting up...")
    # Khởi tạo Redis connection pool sớm để phát hiện lỗi ngay
    await get_redis_client()
    logger.info("✅ Redis connected")
    logger.info("✅ App ready — %s", settings.APP_NAME)

    yield

    # Shutdown
    logger.info("🛑 Shutting down...")
    await close_redis()
    logger.info("✅ Redis closed")


# ── App creation ──────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="LifeQuest Backend API — Gamification platform for real-life quests",
    docs_url="/docs" if settings.DEBUG else None,    # Swagger chỉ ở dev
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── Middleware (thứ tự quan trọng — last added = first executed) ──────────────
# ErrorHandler phải ở ngoài cùng để bắt lỗi từ các middleware khác
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(OnlineTrackingMiddleware)
setup_cors(app)  # CORS phải ở trong cùng (applied first)

# ── Exception handlers ────────────────────────────────────────────────────────

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle FastAPI/Starlette HTTP exceptions → chuẩn hóa response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors → trả lỗi rõ ràng."""
    errors = exc.errors()
    messages = []
    for error in errors:
        field = " → ".join(str(loc) for loc in error["loc"] if loc != "body")
        messages.append(f"{field}: {error['msg']}" if field else error["msg"])

    return JSONResponse(
        status_code=422,
        content={
            "detail": "; ".join(messages),
            "error_code": "VALIDATION_ERROR",
        },
    )


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"], include_in_schema=False)
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
