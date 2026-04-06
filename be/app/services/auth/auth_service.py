from datetime import datetime, timedelta, timezone
import secrets
from uuid import UUID

from fastapi.concurrency import run_in_threadpool
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.exceptions import (
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
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserMeResponse


class AuthService:
    """Business logic cho authentication & authorization."""

    def __init__(self, repository: AuthRepository) -> None:
        self.repository = repository

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
            level_id=1,                          # default level Beginner
        )

        # Tạo UserPreference rỗng — sẽ điền khi onboarding
        await self.repository.create_user_preference(user.id)

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
        current_password: str,
        new_password: str,
    ) -> None:
        """Đổi mật khẩu cho tài khoản local."""
        if user.provider != "local":
            raise ForbiddenException("Google account cannot change password here")

        if user.password_hash is None or not verify_password(current_password, user.password_hash):
            raise CredentialsException("Mật khẩu hiện tại không đúng")

        await self.repository.update_user_password(user, hash_password(new_password))
        await self.repository.commit()

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
