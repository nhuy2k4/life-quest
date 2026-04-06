from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import CurrentUser, get_current_user
from app.deps.db import get_db
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import (
    AuthMessageResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    ResetPasswordRequest,
    ResendOtpRequest,
    RegisterRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserMeResponse
from app.services.auth.auth_service import AuthService
from app.services.email.email_service import EmailService, get_email_service
from app.services.otp.otp_service import OTPService, get_otp_service

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_auth_service(
    db: AsyncSession = Depends(get_db),
    otp_service: OTPService = Depends(get_otp_service),
    email_service: EmailService = Depends(get_email_service),
) -> AuthService:
    repository = AuthRepository(db)
    return AuthService(repository, otp_service=otp_service, email_service=email_service)


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
    service: AuthService = Depends(get_auth_service),
) -> UserMeResponse:
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
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await service.login(request)


@router.post(
    "/google/login",
    response_model=TokenResponse,
    summary="Đăng nhập với Google",
    description="Xác thực Google ID token, đăng nhập hoặc tạo user mới provider=google.",
)
async def login_with_google(
    request: GoogleLoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await service.login_with_google(request.id_token)


@router.post(
    "/verify-email",
    response_model=AuthMessageResponse,
    summary="Xác thực email bằng OTP",
    description="Xác thực OTP gửi đến email, cập nhật user.is_verified=true khi hợp lệ.",
)
async def verify_email(
    request: VerifyEmailRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthMessageResponse:
    return await service.verify_email(request)


@router.post(
    "/resend-otp",
    response_model=AuthMessageResponse,
    summary="Gửi lại OTP xác thực email",
    description="Tạo OTP mới, lưu đè OTP cũ trong Redis và gửi lại qua email.",
)
async def resend_otp(
    request: ResendOtpRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthMessageResponse:
    return await service.resend_otp(request)


@router.post(
    "/change-password",
    response_model=AuthMessageResponse,
    summary="Đổi mật khẩu tài khoản local",
    description="Yêu cầu đăng nhập, chỉ hỗ trợ user provider=local.",
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> AuthMessageResponse:
    return await service.change_password_by_user_id(
        user_id=current_user.id,
        request=request,
    )


@router.post(
    "/forgot-password",
    response_model=AuthMessageResponse,
    summary="Gửi OTP quên mật khẩu",
    description="Tạo OTP reset password cho tài khoản local và gửi qua email.",
)
async def forgot_password(
    request: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthMessageResponse:
    return await service.forgot_password(request)


@router.post(
    "/reset-password",
    response_model=AuthMessageResponse,
    summary="Đặt lại mật khẩu bằng OTP",
    description="Xác thực OTP reset password rồi cập nhật mật khẩu mới cho tài khoản local.",
)
async def reset_password(
    request: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthMessageResponse:
    return await service.reset_password(request)


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
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await service.refresh(request)


# ── POST /auth/logout ─────────────────────────────────────────────────────────

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Đăng xuất",
    description="Thu hồi refresh token trong DB (idempotent).",
)
async def logout(
    body: LogoutRequest,
    service: AuthService = Depends(get_auth_service),
) -> None:
    await service.logout(refresh_token_raw=body.refresh_token)
