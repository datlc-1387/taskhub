from typing import Annotated
from uuid import UUID

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models import TaskPriority, TaskStatus, User, UserRole
from app.repositories.user import UserRepository
from app.schemas.common import Pagination, TaskFilter

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


async def require_admin(user: CurrentUser) -> User:
    if user.role != UserRole.ADMIN:
        raise ForbiddenError("Only an ADMIN can perform this action.")
    return user


AdminUser = Annotated[User, Depends(require_admin)]


def get_pagination(
    page: Annotated[int, Query(ge=1)] = 1, limit: Annotated[int, Query(ge=1, le=100)] = 20
) -> Pagination:
    return Pagination(page=page, limit=limit)


PageParams = Annotated[Pagination, Depends(get_pagination)]


def get_task_filter(
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    assignee_id: UUID | None = None,
) -> TaskFilter:
    return TaskFilter(status=status, priority=priority, assignee_id=assignee_id)


TaskFilterParams = Annotated[TaskFilter, Depends(get_task_filter)]
