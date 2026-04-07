import re
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Request Schemas ───────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr
    password: Annotated[str, Field(min_length=8, max_length=100)]

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username chỉ được chứa chữ cái, số và dấu gạch dưới (_)")
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Mật khẩu phải có ít nhất 1 chữ hoa")
        if not any(c.isdigit() for c in v):
            raise ValueError("Mật khẩu phải có ít nhất 1 chữ số")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "SecurePass1",
            }
        }
    }


class LoginRequest(BaseModel):
    username: str
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "john_doe",
                "password": "SecurePass1",
            }
        }
    }


class RefreshRequest(BaseModel):
    refresh_token: str

    model_config = {
        "json_schema_extra": {
            "example": {"refresh_token": "abc123..."}
        }
    }


class LogoutRequest(BaseModel):
    refresh_token: str


class GoogleLoginRequest(BaseModel):
    id_token: str

    model_config = {
        "json_schema_extra": {
            "example": {"id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ii4uLiJ9..."}
        }
    }


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    otp: Annotated[str, Field(min_length=6, max_length=6)]

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "john@example.com",
                "otp": "123456",
            }
        }
    }


class ResendOtpRequest(BaseModel):
    email: EmailStr

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "john@example.com",
            }
        }
    }


class ChangePasswordRequest(BaseModel):
    current_password: Annotated[str, Field(min_length=8, max_length=100)]
    new_password: Annotated[str, Field(min_length=8, max_length=100)]

    @field_validator("new_password")
    @classmethod
    def new_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Mật khẩu mới phải có ít nhất 1 chữ hoa")
        if not any(c.isdigit() for c in v):
            raise ValueError("Mật khẩu mới phải có ít nhất 1 chữ số")
        return v


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: Annotated[str, Field(min_length=6, max_length=6)]
    new_password: Annotated[str, Field(min_length=8, max_length=100)]

    @field_validator("new_password")
    @classmethod
    def reset_password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Mật khẩu mới phải có ít nhất 1 chữ hoa")
        if not any(c.isdigit() for c in v):
            raise ValueError("Mật khẩu mới phải có ít nhất 1 chữ số")
        return v


# ── Response Schemas ──────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """
    Trả về sau login và refresh.
    onboarding_completed: client dùng để navigate đúng luồng
    (False → OnboardingNavigator, True → MainTabNavigator)
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    onboarding_completed: bool

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "abc123def456...",
                "token_type": "bearer",
                "onboarding_completed": False,
            }
        }
    }


class AuthMessageResponse(BaseModel):
    message: str
