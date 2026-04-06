from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.db import get_db
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserMeResponse
from app.services.auth.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


# ── POST /auth/register ───────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserMeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới",
    description="Tạo tài khoản với username, email và password. Trả về thông tin user vừa tạo.",
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserMeResponse:
    service = AuthService(db)
    return await service.register(request)


# ── POST /auth/login ──────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Đăng nhập",
    description=(
        "Xác thực username + password. Trả access_token (JWT 30 phút) và refresh_token (30 ngày). "
        "Rate limit: 5 request/phút/IP."
    ),
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    return await service.login(request)


# ── POST /auth/refresh ────────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Làm mới token",
    description=(
        "Dùng refresh_token để lấy access_token mới. "
        "Refresh token rotation: token cũ bị thu hồi, token mới được tạo."
    ),
)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(db)
    return await service.refresh(request)


# ── POST /auth/logout ─────────────────────────────────────────────────────────

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Đăng xuất",
    description="Thu hồi access token (Redis blacklist) và refresh token (DB revoke) ngay lập tức.",
)
async def logout(
    body: LogoutRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = AuthService(db)
    access_token = credentials.credentials if credentials else None
    await service.logout(
        access_token=access_token,
        refresh_token_raw=body.refresh_token,
    )
