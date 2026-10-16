from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Label, User, WorkspaceRole
from app.repositories.label import LabelRepository
from app.schemas.label import LabelCreate
from app.services.permissions import PermissionService


class LabelService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = LabelRepository(db)
        self.perms = PermissionService(db)

    async def list_in_project(self, project_id: UUID, user: User) -> list[Label]:
        await self.perms.require_project(project_id, user)
        return list(await self.repo.list_by_project(project_id))

    async def create(self, project_id: UUID, data: LabelCreate, user: User) -> Label:
        await self.perms.require_project(project_id, user, WorkspaceRole.EDITOR)
        return await self.repo.add(Label(project_id=project_id, **data.model_dump()))
