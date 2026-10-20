from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import UnauthorizedError
from app.core.security import hash_password, verify_password
from app.models import User
from app.repositories.refresh_token import RefreshTokenRepository
from app.schemas.user import ChangePasswordRequest, UserUpdate


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.tokens = RefreshTokenRepository(db)

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self.db.flush()
        return user

    async def change_password(self, user: User, data: ChangePasswordRequest) -> None:
        if not await verify_password(data.current_password, user.hashed_password):
            raise UnauthorizedError(messages.CURRENT_PASSWORD_INCORRECT)
        user.hashed_password = await hash_password(data.new_password)
        await self.tokens.revoke_all_for_user(user.id)
