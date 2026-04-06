from datetime import datetime, timedelta, timezone
import secrets
from uuid import UUID

from fastapi.concurrency import run_in_threadpool
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    CredentialsException,
    ForbiddenException,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.core.config import settings
from app.models.user import User
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import (
    AuthMessageResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    ResendOtpRequest,
    RegisterRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.user import UserMeResponse
from app.services.email.email_service import EmailService, get_email_service
from app.services.otp.otp_service import OTPService, get_otp_service


class AuthService:
    """Business logic cho authentication & authorization."""

    def __init__(
        self,
        repository: AuthRepository,
        otp_service: OTPService | None = None,
        email_service: EmailService | None = None,
    ) -> None:
        self.repository = repository
        self.otp_service = otp_service or get_otp_service()
        self.email_service = email_service or get_email_service()

    # ── Register ──────────────────────────────────────────────────────────────

    async def register(self, request: RegisterRequest) -> UserMeResponse:
        """
        Tạo tài khoản mới.

        Steps:
        1. Check email/username unique
        2. Hash password (bcrypt cost=12)
        3. Tạo User + UserPreference rỗng (chuẩn bị cho onboarding)
        4. Commit → trả UserMeResponse
        """
        # Check email đã tồn tại
        existing_user_by_email = await self.repository.get_user_by_email(request.email)
        if existing_user_by_email:
            raise ConflictException("Email đã được sử dụng")

        # Check username đã tồn tại
        existing_user_by_username = await self.repository.get_user_by_username(
            request.username
        )
        if existing_user_by_username:
            raise ConflictException("Username đã được sử dụng")

        # Tạo user mới
        user = await self.repository.create_user(
            username=request.username,
            email=request.email,
            password_hash=hash_password(request.password),
            provider="local",
            provider_id=None,
            is_verified=False,
            level_id=1,                          # default level Beginner
        )

        # Tạo UserPreference rỗng — sẽ điền khi onboarding
        await self.repository.create_user_preference(user.id)

        await self._generate_and_send_email_otp(request.email)

        await self.repository.commit()
        await self.repository.refresh_user(user)
        return UserMeResponse.model_validate(user)

    # ── Login ─────────────────────────────────────────────────────────────────

    async def login(self, request: LoginRequest) -> TokenResponse:
        """
        Xác thực và phát JWT + refresh token.

        Returns:
            TokenResponse với onboarding_completed — mobile dùng để navigate
        """
        # Tìm user theo username
        user = await self.repository.get_user_by_username(request.username)

        if user is not None and user.provider != "local":
            raise CredentialsException("Please login with Google")

        # Trả cùng 1 lỗi cho "không tìm thấy" và "sai mật khẩu"
        # để tránh username enumeration attack
        if user is None or user.password_hash is None:
            raise CredentialsException("Username hoặc mật khẩu không đúng")

        if not verify_password(request.password, user.password_hash):
            raise CredentialsException("Username hoặc mật khẩu không đúng")

        if user.is_banned:
            raise ForbiddenException("Tài khoản đã bị khóa. Liên hệ support để được hỗ trợ.")

        if not user.is_verified:
            raise ForbiddenException("Please verify your email first")

        token_response = await self._issue_tokens(user)
        await self.repository.commit()
        return token_response

    async def login_with_google(self, id_token_raw: str) -> TokenResponse:
        """Đăng nhập bằng Google ID token, tự tạo user mới nếu chưa tồn tại."""
        if not settings.GOOGLE_OAUTH_CLIENT_ID:
            raise CredentialsException("Google login chưa được cấu hình")

        try:
            token_info = await run_in_threadpool(
                google_id_token.verify_oauth2_token,
                id_token_raw,
                google_requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID,
            )
        except Exception as exc:
            raise CredentialsException("Google token không hợp lệ") from exc

        email = token_info.get("email")
        provider_id = token_info.get("sub")
        if not email or not provider_id:
            raise CredentialsException("Google token thiếu thông tin cần thiết")

        user = await self.repository.get_user_by_email(email)

        if user is None:
            username = await self._generate_unique_username()
            user = await self.repository.create_user(
                username=username,
                email=email,
                password_hash=None,
                provider="google",
                provider_id=provider_id,
                is_verified=True,
                level_id=1,
            )
            await self.repository.create_user_preference(user.id)

        if user.is_banned:
            raise ForbiddenException("Tài khoản đã bị khóa")

        token_response = await self._issue_tokens(user)
        await self.repository.commit()
        return token_response

    # ── Refresh ───────────────────────────────────────────────────────────────

    async def refresh(self, request: RefreshRequest) -> TokenResponse:
        """
        Xoay vòng refresh token — thu hồi cũ, tạo mới.

        Security: Refresh token rotation — mỗi lần refresh tạo token mới,
        vô hiệu hóa token cũ ngay lập tức.
        """
        token_hash = hash_refresh_token(request.refresh_token.strip())

        db_token = await self.repository.get_refresh_token(token_hash)

        if db_token is None:
            raise CredentialsException("Refresh token không hợp lệ hoặc đã hết hạn")

        if db_token.is_revoked:
            await self._handle_token_reuse(db_token)

        if not db_token.is_valid:
            raise CredentialsException("Refresh token không hợp lệ hoặc đã hết hạn")

        # Lấy user để kiểm tra ban status
        user = await self.repository.get_user_by_id(db_token.user_id)

        if user is None:
            raise CredentialsException("User không tồn tại")

        if user.is_banned:
            raise ForbiddenException("Tài khoản đã bị khóa")

        # Thu hồi token cũ
        await self.repository.revoke_refresh_token(db_token)

        # Tạo token mới
        token_response = await self._issue_tokens(user)

        await self.repository.commit()

        return token_response

    # ── Logout ────────────────────────────────────────────────────────────────

    async def logout(self, refresh_token_raw: str) -> None:
        """
        Thu hồi refresh token hiện tại trong DB.
        Nếu token không hợp lệ/đã revoke/đã hết hạn thì bỏ qua (idempotent logout).
        """
        # Revoke refresh token trong DB
        token_hash = hash_refresh_token(refresh_token_raw.strip())
        db_token = await self.repository.get_refresh_token(token_hash)

        if db_token is None:
            return

        if db_token.is_revoked or not db_token.is_valid:
            return

        await self.repository.revoke_refresh_token(db_token)
        await self.repository.commit()

    async def _handle_token_reuse(self, db_token) -> None:
        """Handle refresh token reuse: revoke all user tokens and raise 401."""
        await self._revoke_all_user_refresh_tokens(db_token.user_id)
        await self.repository.commit()
        raise CredentialsException("Phát hiện token reuse. Vui lòng đăng nhập lại")

    async def _generate_unique_username(self) -> str:
        """Tạo username ngẫu nhiên và đảm bảo unique trong DB."""
        for _ in range(20):
            candidate = f"user_{secrets.token_hex(3)}"
            if await self.repository.get_user_by_username(candidate) is None:
                return candidate
        raise ConflictException("Không thể tạo username duy nhất, vui lòng thử lại")

    async def change_password(
        self,
        user: User,
        request: ChangePasswordRequest,
    ) -> AuthMessageResponse:
        """Đổi mật khẩu cho tài khoản local."""
        if user.provider != "local":
            raise ForbiddenException("Google account cannot change password here")

        if user.password_hash is None or not verify_password(request.current_password, user.password_hash):
            raise CredentialsException("Mật khẩu hiện tại không đúng")

        if request.current_password == request.new_password:
            raise BadRequestException("Mật khẩu mới không được trùng mật khẩu cũ")

        await self.repository.update_user_password(user, hash_password(request.new_password))
        await self.repository.commit()
        return AuthMessageResponse(message="Password changed successfully")

    async def change_password_by_user_id(
        self,
        user_id: UUID,
        request: ChangePasswordRequest,
    ) -> AuthMessageResponse:
        user = await self.repository.get_user_by_id(user_id)
        if user is None:
            raise CredentialsException("User không tồn tại")
        return await self.change_password(user=user, request=request)

    async def forgot_password(self, request: ForgotPasswordRequest) -> AuthMessageResponse:
        user = await self.repository.get_user_by_email(request.email)

        # Không tiết lộ email có tồn tại hay không.
        if user is None:
            return AuthMessageResponse(
                message="If this email exists, a reset OTP has been sent"
            )

        if user.provider != "local":
            raise BadRequestException("Please login with Google")

        await self.otp_service.enforce_reset_password_cooldown(request.email)

        otp = self.otp_service.generate_otp()
        await self.otp_service.save_reset_password_otp(request.email, otp)
        await self.email_service.send_reset_password_otp_email(request.email, otp)
        await self.otp_service.mark_reset_password_cooldown(request.email)

        return AuthMessageResponse(
            message="If this email exists, a reset OTP has been sent"
        )

    async def reset_password(self, request: ResetPasswordRequest) -> AuthMessageResponse:
        user = await self.repository.get_user_by_email(request.email)
        if user is None:
            raise BadRequestException("Email does not exist")

        if user.provider != "local":
            raise BadRequestException("Please login with Google")

        await self.otp_service.verify_reset_password_otp(request.email, request.otp)
        await self.repository.update_user_password(user, hash_password(request.new_password))
        await self.otp_service.delete_reset_password_otp(request.email)
        await self.repository.commit()

        return AuthMessageResponse(message="Password reset successfully")

    async def verify_email(self, request: VerifyEmailRequest) -> AuthMessageResponse:
        user = await self.repository.get_user_by_email(request.email)
        if user is None:
            raise BadRequestException("Email does not exist")

        if user.is_verified:
            return AuthMessageResponse(message="Email already verified")

        await self.otp_service.verify_otp(request.email, request.otp)
        await self.repository.set_user_verified(user, True)
        await self.otp_service.delete_otp(request.email)
        await self.repository.commit()

        return AuthMessageResponse(message="Email verified successfully")

    async def resend_otp(self, request: ResendOtpRequest) -> AuthMessageResponse:
        user = await self.repository.get_user_by_email(request.email)
        if user is None:
            raise BadRequestException("Email does not exist")

        if user.is_verified:
            return AuthMessageResponse(message="Email already verified")

        await self.otp_service.enforce_resend_cooldown(request.email)
        await self._generate_and_send_email_otp(request.email)
        await self.otp_service.mark_resend_cooldown(request.email)

        return AuthMessageResponse(message="OTP has been resent")

    # ── Private Helpers ───────────────────────────────────────────────────────

    async def _issue_tokens(self, user: User) -> TokenResponse:
        """
        Tạo access token + refresh token và lưu refresh token vào DB.
        Dùng chung cho login và refresh.
        """
        # Tạo access token (JWT, 30 phút)
        access_token = create_access_token(
            user_id=user.id,
            role=user.role,
        )

        # Tạo refresh token (opaque, 30 ngày)
        raw_refresh, refresh_hash = create_refresh_token()

        expire_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_expires = datetime.now(timezone.utc) + expire_delta

        await self.repository.create_refresh_token(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=refresh_expires,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            onboarding_completed=user.onboarding_completed,
        )

    async def _revoke_all_user_refresh_tokens(self, user_id: UUID) -> None:
        """Emergency revoke tất cả refresh token của user khi phát hiện reuse attack."""
        await self.repository.revoke_all_user_tokens(user_id)

    async def _generate_and_send_email_otp(self, email: str) -> None:
        otp = self.otp_service.generate_otp()
        await self.otp_service.save_otp_to_redis(email, otp)
        await self.email_service.send_otp_email(email, otp)
