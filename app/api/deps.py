from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{get_settings().api_v1_prefix}/auth/login")
DbSession = Annotated[AsyncSession, Depends(get_db, scope="function")]


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbSession) -> User:
    try:
        payload = decode_token(token, expected_type="access")
    except ValueError as exc:
        raise UnauthorizedError(str(exc)) from exc
    user = await UserRepository(db).get(payload.user_id)
    if user is None:
        raise UnauthorizedError("User doesn't exist.")
    if not user.is_active:
        raise ForbiddenError("The account has been locked.")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
