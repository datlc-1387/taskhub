from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Workspace, WorkspaceMember, WorkspaceRole
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate
from app.services.permissions import PermissionService


class WorkspaceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = WorkspaceRepository(db)
        self.perms = PermissionService(db)

    async def create(self, data: WorkspaceCreate, owner: User) -> Workspace:
        workspace = await self.repo.add(Workspace(name=data.name, owner_id=owner.id))
        await self.repo.add_member(
            WorkspaceMember(workspace_id=workspace.id, user_id=owner.id, role=WorkspaceRole.OWNER)
        )
        return workspace

    async def update(self, workspace_id: UUID, data: WorkspaceUpdate, user: User) -> Workspace:
        workspace = await self.perms.require_workspace(workspace_id, user, WorkspaceRole.OWNER)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(workspace, field, value)
        await self.db.flush()
        return workspace

    async def delete(self, workspace_id: UUID, user: User) -> None:
        workspace = await self.perms.require_workspace(workspace_id, user, WorkspaceRole.OWNER)
        await self.repo.delete(workspace)

    async def list_mine(self, user: User) -> list[Workspace]:
        return list(await self.repo.list_for_user(user.id))

    async def get(self, workspace_id: UUID, user: User) -> Workspace:
        return await self.perms.require_workspace(workspace_id, user)
