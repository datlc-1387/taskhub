from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models import Project, User, UserRole, Workspace, WorkspaceRole
from app.repositories.project import ProjectRepository
from app.repositories.workspace import WorkspaceRepository

ROLE_RANK: dict[WorkspaceRole, int] = {
    WorkspaceRole.VIEWER: 1,
    WorkspaceRole.EDITOR: 2,
    WorkspaceRole.OWNER: 3,
}


class PermissionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.workspaces = WorkspaceRepository(db)
        self.projects = ProjectRepository(db)

    async def role_in_workspace(self, workspace_id: UUID, user: User) -> WorkspaceRole | None:
        if user.role == UserRole.ADMIN:
            return WorkspaceRole.OWNER

        member = await self.workspaces.get_member(workspace_id, user.id)
        return member.role if member else None

    async def require_workspace(
        self, workspace_id: UUID, user: User, min_role: WorkspaceRole = WorkspaceRole.VIEWER
    ) -> Workspace:
        workspace = await self.workspaces.get(workspace_id)
        if workspace is None:
            raise NotFoundError(f"Workspace {workspace_id} does not exist.")
        role = await self.role_in_workspace(workspace_id, user)
        if role is None:
            raise NotFoundError(f"Workspace {workspace_id} does not exist.")
        if ROLE_RANK[role] < ROLE_RANK[min_role]:
            raise ForbiddenError(f"Requires the {min_role} role or higher within the workspace")
        return workspace

    async def require_project(
        self, project_id: UUID, user: User, min_role: WorkspaceRole = WorkspaceRole.VIEWER
    ) -> Project:
        project = await self.projects.get(project_id)
        if project is None:
            raise NotFoundError(f"Project {project_id} does not exist.")
        await self.require_workspace(project.workspace_id, user, min_role)
        return project
