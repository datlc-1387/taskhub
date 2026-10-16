from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, User, WorkspaceRole
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate
from app.services.permissions import PermissionService


class ProjectService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ProjectRepository(db)
        self.perms = PermissionService(db)

    async def create(self, workspace_id: UUID, data: ProjectCreate, user: User) -> Project:
        await self.perms.require_workspace(workspace_id, user, WorkspaceRole.EDITOR)
        return await self.repo.add(Project(workspace_id=workspace_id, **data.model_dump()))

    async def list_in_workspace(self, workspace_id: UUID, user: User) -> list[Project]:
        await self.perms.require_workspace(workspace_id, user, WorkspaceRole.VIEWER)
        return list(await self.repo.list_by_workspace(workspace_id))
