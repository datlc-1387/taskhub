from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository

DbSession = Annotated[AsyncSession, Depends(get_db, scope="function")]


async def get_current_user(db: DbSession) -> User:
    # TODO: get user from token payload
    user = await UserRepository(db).get(UUID("a4d060c4-f7e8-4f90-802c-f17f64433763"))
    if user is None:
        raise UnauthorizedError("User doesn't exist.")
    if not user.is_active:
        raise ForbiddenError("The account has been locked.")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
