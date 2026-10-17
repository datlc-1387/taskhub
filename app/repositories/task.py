from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    model = Task

    async def get_with_project(self, task_id: UUID) -> Task | None:
        stmt = (
            select(Task)
            .options(joinedload(Task.project))
            .where(Task.id == task_id)
            .order_by(Task.created_at)
        )
        return await self.db.scalar(stmt)

    async def list_by_project(self, project_id: UUID) -> Sequence[Task]:
        conditions = [Task.project_id == project_id]
        stmt = select(Task).where(*conditions).order_by(Task.created_at.desc())
        items = (await self.db.scalars(stmt)).all()
        return items
