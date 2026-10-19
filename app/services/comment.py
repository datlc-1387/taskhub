from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models import Comment, User, UserRole, WorkspaceRole
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
        await self.perms.require_task(task_id, user)
        return await self.repo.add(
            Comment(task_id=task_id, author_id=user.id, content=data.content)
        )

    async def delete(self, task_id: UUID, comment_id: UUID, user: User) -> None:
        task = await self.perms.require_task(task_id, user)
        comment = await self.repo.get(comment_id)
        if comment is None or comment.task_id != task_id:
            raise NotFoundError(f"Comment {comment_id} does not exist")
        role = await self.perms.role_in_workspace(task.project.workspace_id, user)
        is_owner = role == WorkspaceRole.OWNER or user.role == UserRole.ADMIN
        if comment.author_id != user.id and not is_owner:
            raise ForbiddenError("Only the author or the OWNER can delete a comment")
        await self.repo.delete(comment)
