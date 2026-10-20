from uuid import UUID

from sqlalchemy import update

from app.models import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    model = RefreshToken

    async def revoke_if_active(self, jti: str) -> UUID | None:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.jti == jti, RefreshToken.revoked.is_(False))
            .values(revoked=True)
            .returning(RefreshToken.user_id)
        )
        user_id = await self.db.scalar(stmt)
        return user_id

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        await self.db.execute(
            update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked=True)
        )
