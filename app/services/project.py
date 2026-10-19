from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Project, ProjectStatus, User, WorkspaceRole
from app.repositories.project import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
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

    async def get(self, project_id: UUID, user: User) -> Project:
        return await self.perms.require_project(project_id, user)

    async def update(self, project_id: UUID, data: ProjectUpdate, user: User) -> Project:
        project = await self.perms.require_project(project_id, user, WorkspaceRole.EDITOR)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        await self.db.flush()
        return project

    async def delete(self, project_id: UUID, user: User) -> None:
        project = await self.perms.require_project(project_id, user, WorkspaceRole.OWNER)
        await self.repo.delete(project)

    async def archive(self, project_id: UUID, user: User) -> Project:
        project = await self.perms.require_project(project_id, user, WorkspaceRole.EDITOR)
        project.status = ProjectStatus.ARCHIVED
        await self.db.flush()
        return project
