from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import RefreshToken
from app.models.user import User
from app.models.user_preference import UserPreference


class AuthRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(
        self,
        username: str,
        email: str,
        password_hash: str | None,
        provider: str = "local",
        provider_id: str | None = None,
        level_id: int = 1,
    ) -> User:
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            provider=provider,
            provider_id=provider_id,
            level_id=level_id,
        )
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_user_password(self, user: User, password_hash: str) -> None:
        user.password_hash = password_hash
        await self.db.flush()

    async def create_user_preference(self, user_id: UUID) -> UserPreference:
        preference = UserPreference(user_id=user_id)
        self.db.add(preference)
        await self.db.flush()
        return preference

    async def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def create_refresh_token(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(refresh_token)
        await self.db.flush()
        return refresh_token

    async def revoke_refresh_token(self, token: RefreshToken) -> None:
        token.is_revoked = True
        await self.db.flush()

    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked.is_(False),
            )
            .values(is_revoked=True)
        )

    async def commit(self) -> None:
        await self.db.commit()

    async def refresh_user(self, user: User) -> None:
        await self.db.refresh(user)
