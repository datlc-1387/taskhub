from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.models import Task
from app.repositories.base import BaseRepository
from app.schemas.common import Pagination
from app.schemas.task import TaskFilter


class TaskRepository(BaseRepository[Task]):
    model = Task

    async def get_with_project(self, task_id: UUID) -> Task | None:
        stmt = select(Task).options(joinedload(Task.project)).where(Task.id == task_id)
        return await self.db.scalar(stmt)

    async def list_by_project(
        self, project_id: UUID, filters: TaskFilter, page: Pagination
    ) -> tuple[Sequence[Task], int]:
        conditions = [Task.project_id == project_id]
        if filters.status is not None:
            conditions.append(Task.status == filters.status)
        if filters.priority is not None:
            conditions.append(Task.priority == filters.priority)
        if filters.assignee_id is not None:
            conditions.append(Task.assignee_id == filters.assignee_id)

        total = await self.db.scalar(select(func.count()).select_from(Task).where(*conditions))
        stmt = (
            select(Task)
            .where(*conditions)
            .offset(page.offset)
            .limit(page.limit)
            .order_by(Task.created_at.desc(), Task.id)
        )
        items = (await self.db.scalars(stmt)).all()
        return items, total or 0
