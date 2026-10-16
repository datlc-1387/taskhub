from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from app.models import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    model = Project

    async def list_by_workspace(self, workspace_id: UUID) -> Sequence[Project]:
        stmt = (
            select(Project).where(Project.workspace_id == workspace_id).order_by(Project.created_at)
        )
        return (await self.db.scalars(stmt)).all()
