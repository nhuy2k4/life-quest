import hashlib
import hmac
import secrets

from app.core.config import settings
from app.core.exceptions import BadRequestException, RateLimitException
from app.core.redis import redis_delete, redis_get, redis_set


class OTPService:
    """Handle OTP generation, storage, and verification for email flows."""

    def __init__(
        self,
        otp_ttl_seconds: int = 300,
        resend_cooldown_seconds: int = 60,
    ) -> None:
        self.otp_ttl_seconds = otp_ttl_seconds
        self.resend_cooldown_seconds = resend_cooldown_seconds

    @staticmethod
    def _otp_key(email: str) -> str:
        return f"otp:verify_email:{email.lower()}"

    @staticmethod
    def _cooldown_key(email: str) -> str:
        return f"otp:verify_email:cooldown:{email.lower()}"

    @staticmethod
    def _reset_password_key(email: str) -> str:
        return f"otp:reset_password:{email.lower()}"

    @staticmethod
    def _reset_password_cooldown_key(email: str) -> str:
        return f"otp:reset_password:cooldown:{email.lower()}"

    @staticmethod
    def generate_otp() -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    @staticmethod
    def _hash_otp(otp: str) -> str:
        # Hash OTP with keyed HMAC to avoid storing raw OTP in Redis.
        return hmac.new(
            key=settings.JWT_SECRET_KEY.encode("utf-8"),
            msg=otp.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

    async def save_otp_to_redis(self, email: str, otp: str) -> None:
        key = self._otp_key(email)
        await redis_set(key, self._hash_otp(otp), ttl=self.otp_ttl_seconds)

    async def verify_otp(self, email: str, otp: str) -> None:
        key = self._otp_key(email)
        cached_hash = await redis_get(key)
        if cached_hash is None:
            raise BadRequestException("OTP expired")

        if not hmac.compare_digest(cached_hash, self._hash_otp(otp)):
            raise BadRequestException("Invalid OTP")

    async def delete_otp(self, email: str) -> None:
        await redis_delete(self._otp_key(email))

    async def enforce_resend_cooldown(self, email: str) -> None:
        cooldown_key = self._cooldown_key(email)
        if await redis_get(cooldown_key):
            raise RateLimitException("Please wait before requesting another OTP")

    async def mark_resend_cooldown(self, email: str) -> None:
        cooldown_key = self._cooldown_key(email)
        await redis_set(cooldown_key, "1", ttl=self.resend_cooldown_seconds)

    async def save_reset_password_otp(self, email: str, otp: str) -> None:
        await redis_set(
            self._reset_password_key(email),
            self._hash_otp(otp),
            ttl=self.otp_ttl_seconds,
        )

    async def verify_reset_password_otp(self, email: str, otp: str) -> None:
        cached_hash = await redis_get(self._reset_password_key(email))
        if cached_hash is None:
            raise BadRequestException("OTP expired")

        if not hmac.compare_digest(cached_hash, self._hash_otp(otp)):
            raise BadRequestException("Invalid OTP")

    async def delete_reset_password_otp(self, email: str) -> None:
        await redis_delete(self._reset_password_key(email))

    async def enforce_reset_password_cooldown(self, email: str) -> None:
        if await redis_get(self._reset_password_cooldown_key(email)):
            raise RateLimitException("Please wait before requesting another OTP")

    async def mark_reset_password_cooldown(self, email: str) -> None:
        await redis_set(
            self._reset_password_cooldown_key(email),
            "1",
            ttl=self.resend_cooldown_seconds,
        )



def get_otp_service() -> OTPService:
    return OTPService(
        otp_ttl_seconds=settings.OTP_VERIFY_EMAIL_TTL_SECONDS,
        resend_cooldown_seconds=settings.OTP_RESEND_COOLDOWN_SECONDS,
    )
