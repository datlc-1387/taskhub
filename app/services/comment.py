from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Comment, User
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
