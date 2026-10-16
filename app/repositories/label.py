from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from app.models import Label
from app.repositories.base import BaseRepository


class LabelRepository(BaseRepository[Label]):
    model = Label

    async def list_by_project(self, project_id: UUID) -> Sequence[Label]:
        stmt = select(Label).where(Label.project_id == project_id).order_by(Label.name)
        return (await self.db.scalars(stmt)).all()
