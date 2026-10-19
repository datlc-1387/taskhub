from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import RefreshToken, User
from app.repositories.user import RefreshTokenRepository, UserRepository
from app.schemas.auth import RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.tokens = RefreshTokenRepository(db)

    async def register(self, data: RegisterRequest) -> User:
        if await self.users.get_user_by_email(data.email) is not None:
            raise ConflictError("Email already registered")
        user = User(
            email=data.email, full_name=data.full_name, hashed_password=hash_password(data.password)
        )
        return await self.users.add(user)

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self.users.get_user_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Incorrect email or password")
        if not user.is_active:
            raise UnauthorizedError("Your account has been locked")
        return await self._issue_tokens(user.id)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        stored = await self._validate_refresh(refresh_token)
        stored.revoked = True
        return await self._issue_tokens(stored.user_id)

    async def logout(self, refresh_token: str) -> None:
        stored = await self._validate_refresh(refresh_token)
        stored.revoked = True

    async def _issue_tokens(self, user_id: UUID) -> TokenResponse:
        access_token, _ = create_access_token(user_id)
        refresh_token, payload = create_refresh_token(user_id)
        await self.tokens.add(
            RefreshToken(jti=payload.jti, user_id=user_id, expires_at=payload.exp)
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=get_settings().access_token_expire_minutes * 60,
        )

    async def _validate_refresh(self, refresh_token: str) -> RefreshToken:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except ValueError as exc:
            raise UnauthorizedError(str(exc)) from exc
        stored = await self.tokens.get_by_jti(payload.jti)
        if stored is None or stored.revoked:
            raise UnauthorizedError("The refresh token has been revoked")
        return stored
