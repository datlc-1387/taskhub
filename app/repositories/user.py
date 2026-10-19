from uuid import UUID

from sqlalchemy import select, update

from app.models import RefreshToken, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.db.scalar(select(User).where(User.email == email))


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    model = RefreshToken

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        return await self.db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self.db.execute(
            update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked=True)
        )
