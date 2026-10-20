from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import NotFoundError
from app.models import Comment, User, WorkspaceRole
from app.repositories.comment import CommentRepository
from app.schemas.comment import CommentCreate
from app.services.permissions import PermissionService


class CommentService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = CommentRepository(db)
        self.perms = PermissionService(db)

    async def list_for_task(self, task_id: UUID, user: User) -> list[Comment]:
        await self.perms.require_task(task_id, user)
        return list(await self.repo.list_by_task(task_id))

    async def add(self, task_id: UUID, data: CommentCreate, user: User) -> Comment:
        await self.perms.require_task(task_id, user, writable=True)
        return await self.repo.add(
            Comment(task_id=task_id, author_id=user.id, content=data.content)
        )

    async def delete(self, task_id: UUID, comment_id: UUID, user: User) -> None:
        _, role = await self.perms.require_task_with_role(task_id, user, writable=True)
        comment = await self.repo.get(comment_id)
        if comment is None or comment.task_id != task_id:
            raise NotFoundError(messages.COMMENT_NOT_FOUND.format(comment_id=comment_id))
        self.perms.require_author_or_role(
            user, comment.author_id, role, WorkspaceRole.OWNER, messages.COMMENT_DELETE_FORBIDDEN
        )
        await self.repo.delete(comment)
