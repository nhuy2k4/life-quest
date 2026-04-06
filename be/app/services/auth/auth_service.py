from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ConflictException,
    CredentialsException,
    ForbiddenException,
)
from app.core.security import (
    blacklist_token,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.core.config import settings
from app.models.auth import RefreshToken
from app.models.user import User
from app.models.user_preference import UserPreference
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserMeResponse


class AuthService:
    """Business logic cho authentication & authorization."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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
        result = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        if result.scalar_one_or_none():
            raise ConflictException("Email đã được sử dụng")

        # Check username đã tồn tại
        result = await self.db.execute(
            select(User).where(User.username == request.username)
        )
        if result.scalar_one_or_none():
            raise ConflictException("Username đã được sử dụng")

        # Tạo user mới
        user = User(
            username=request.username,
            email=request.email,
            password_hash=hash_password(request.password),
            level_id=1,                          # default level Beginner
        )
        self.db.add(user)
        await self.db.flush()  # flush để lấy user.id cho UserPreference

        # Tạo UserPreference rỗng — sẽ điền khi onboarding
        preference = UserPreference(user_id=user.id)
        self.db.add(preference)

        await self.db.commit()
        await self.db.refresh(user)

        return UserMeResponse.model_validate(user)

    # ── Login ─────────────────────────────────────────────────────────────────

    async def login(self, request: LoginRequest) -> TokenResponse:
        """
        Xác thực và phát JWT + refresh token.

        Returns:
            TokenResponse với onboarding_completed — mobile dùng để navigate
        """
        # Tìm user theo username
        result = await self.db.execute(
            select(User).where(User.username == request.username)
        )
        user = result.scalar_one_or_none()

        # Trả cùng 1 lỗi cho "không tìm thấy" và "sai mật khẩu"
        # để tránh username enumeration attack
        if user is None or not verify_password(request.password, user.password_hash):
            raise CredentialsException("Username hoặc mật khẩu không đúng")

        if user.is_banned:
            raise ForbiddenException("Tài khoản đã bị khóa. Liên hệ support để được hỗ trợ.")

        token_response = await self._issue_tokens(user)
        await self.db.commit()
        return token_response

    # ── Refresh ───────────────────────────────────────────────────────────────

    async def refresh(self, request: RefreshRequest) -> TokenResponse:
        """
        Xoay vòng refresh token — thu hồi cũ, tạo mới.

        Security: Refresh token rotation — mỗi lần refresh tạo token mới,
        vô hiệu hóa token cũ ngay lập tức.
        """
        token_hash = hash_refresh_token(request.refresh_token.strip())

        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        db_token = result.scalar_one_or_none()

        if db_token is None:
            raise CredentialsException("Refresh token không hợp lệ hoặc đã hết hạn")

        if db_token.is_revoked:
            # Reuse token đã bị thu hồi => nghi ngờ token theft, thu hồi toàn bộ session user.
            await self._revoke_all_user_refresh_tokens(db_token.user_id)
            await self.db.commit()
            raise CredentialsException("Phát hiện token reuse. Vui lòng đăng nhập lại")

        if not db_token.is_valid:
            raise CredentialsException("Refresh token không hợp lệ hoặc đã hết hạn")

        # Lấy user để kiểm tra ban status
        result = await self.db.execute(
            select(User).where(User.id == db_token.user_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            raise CredentialsException("User không tồn tại")

        if user.is_banned:
            raise ForbiddenException("Tài khoản đã bị khóa")

        # Thu hồi token cũ
        db_token.is_revoked = True
        await self.db.flush()

        # Tạo token mới
        token_response = await self._issue_tokens(user)

        await self.db.commit()

        return token_response

    # ── Logout ────────────────────────────────────────────────────────────────

    async def logout(self, access_token: str | None, refresh_token_raw: str) -> None:
        """
        Thu hồi cả access token (Redis blacklist) và refresh token (DB revoke).

        Logout có hiệu lực ngay lập tức — không cần chờ token hết hạn.
        """
        # Blacklist access token trong Redis (nếu client có gửi)
        if access_token:
            try:
                payload = decode_access_token(access_token)
                jti = payload.get("jti")
                exp = payload.get("exp")
                if jti and exp:
                    expire_at = datetime.fromtimestamp(exp, tz=timezone.utc)
                    await blacklist_token(jti, expire_at)
            except jwt.InvalidTokenError:
                # Token không hợp lệ — bỏ qua, vẫn revoke refresh token
                pass

        # Revoke refresh token trong DB
        token_hash = hash_refresh_token(refresh_token_raw.strip())
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        db_token = result.scalar_one_or_none()

        if db_token is None:
            raise CredentialsException("Refresh token không hợp lệ hoặc đã hết hạn")

        if db_token.is_revoked:
            # Token đã revoke nhưng vẫn bị dùng lại => thu hồi toàn bộ refresh token của user.
            await self._revoke_all_user_refresh_tokens(db_token.user_id)
            await self.db.commit()
            raise CredentialsException("Phát hiện token reuse. Vui lòng đăng nhập lại")

        if not db_token.is_valid:
            raise CredentialsException("Refresh token không hợp lệ hoặc đã hết hạn")

        db_token.is_revoked = True

        await self.db.commit()

    # ── Private Helpers ───────────────────────────────────────────────────────

    async def _issue_tokens(self, user: User) -> TokenResponse:
        """
        Tạo access token + refresh token và lưu refresh token vào DB.
        Dùng chung cho login và refresh.
        """
        # Tạo access token (JWT, 30 phút)
        access_token, jti = create_access_token(
            user_id=user.id,
            role=user.role,
        )

        # Tạo refresh token (opaque, 30 ngày)
        raw_refresh, refresh_hash = create_refresh_token()

        expire_delta = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_expires = datetime.now(timezone.utc) + expire_delta

        db_refresh = RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=refresh_expires,
        )
        self.db.add(db_refresh)
        await self.db.flush()

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            onboarding_completed=user.onboarding_completed,
        )

    async def _revoke_all_user_refresh_tokens(self, user_id) -> None:
        """Emergency revoke tất cả refresh token của user khi phát hiện reuse attack."""
        await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked.is_(False),
            )
            .values(is_revoked=True)
        )
