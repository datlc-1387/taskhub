from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models import Project, ProjectStatus, Task, User, UserRole, Workspace, WorkspaceRole
from app.repositories.project import ProjectRepository
from app.repositories.task import TaskRepository
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
        self.tasks = TaskRepository(db)

    async def role_in_workspace(self, workspace_id: UUID, user: User) -> WorkspaceRole | None:
        if user.role == UserRole.ADMIN:
            return WorkspaceRole.OWNER

        member = await self.workspaces.get_member(workspace_id, user.id)
        return member.role if member else None

    async def require_workspace(
        self, workspace_id: UUID, user: User, min_role: WorkspaceRole = WorkspaceRole.VIEWER
    ) -> Workspace:
        workspace, _ = await self._require_role(workspace_id, user, min_role)
        return workspace

    async def require_project(
        self,
        project_id: UUID,
        user: User,
        min_role: WorkspaceRole = WorkspaceRole.VIEWER,
        *,
        writable: bool = False,
    ) -> Project:
        project = await self.projects.get(project_id)
        if project is None:
            raise NotFoundError(messages.PROJECT_NOT_FOUND.format(project_id=project_id))
        await self.require_workspace(project.workspace_id, user, min_role)
        if writable:
            self._ensure_not_archived(project)
        return project

    async def require_task(
        self,
        task_id: UUID,
        user: User,
        min_role: WorkspaceRole = WorkspaceRole.VIEWER,
        *,
        writable: bool = False,
    ) -> Task:
        task, _ = await self.require_task_with_role(task_id, user, min_role, writable=writable)
        return task

    async def require_task_with_role(
        self,
        task_id: UUID,
        user: User,
        min_role: WorkspaceRole = WorkspaceRole.VIEWER,
        *,
        writable: bool = False,
    ) -> tuple[Task, WorkspaceRole]:
        task = await self.tasks.get_with_project(task_id)
        if task is None:
            raise NotFoundError(messages.TASK_NOT_FOUND.format(task_id=task_id))
        _, role = await self._require_role(task.project.workspace_id, user, min_role)
        if writable:
            self._ensure_not_archived(task.project)
        return task, role

    @staticmethod
    def require_author_or_role(
        user: User, author_id: UUID, role: WorkspaceRole, min_role: WorkspaceRole, message: str
    ) -> None:
        if author_id != user.id and ROLE_RANK[role] < ROLE_RANK[min_role]:
            raise ForbiddenError(message)

    @staticmethod
    def _ensure_not_archived(project: Project) -> None:
        if project.status == ProjectStatus.ARCHIVED:
            raise ConflictError(messages.PROJECT_ARCHIVED.format(project_id=project.id))

    async def _require_role(
        self, workspace_id: UUID, user: User, min_role: WorkspaceRole
    ) -> tuple[Workspace, WorkspaceRole]:
        workspace = await self.workspaces.get(workspace_id)
        if workspace is None:
            raise NotFoundError(messages.WORKSPACE_NOT_FOUND.format(workspace_id=workspace_id))
        role = await self.role_in_workspace(workspace_id, user)
        if role is None:
            raise NotFoundError(messages.WORKSPACE_NOT_FOUND.format(workspace_id=workspace_id))
        if ROLE_RANK[role] < ROLE_RANK[min_role]:
            raise ForbiddenError(messages.ROLE_REQUIRED.format(role=min_role))
        return workspace, role
