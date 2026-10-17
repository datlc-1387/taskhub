from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from app.models import Comment
from app.repositories.base import BaseRepository


class CommentRepository(BaseRepository[Comment]):
    model = Comment

    async def list_by_task(self, task_id: UUID) -> Sequence[Comment]:
        stmt = select(Comment).where(Comment.task_id == task_id).order_by(Comment.created_at)
        return (await self.db.scalars(stmt)).all()
