from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Workspace, WorkspaceMember, WorkspaceRole
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import WorkspaceCreate


class WorkspaceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = WorkspaceRepository(db)

    async def create(self, data: WorkspaceCreate, owner: User) -> Workspace:
        workspace = await self.repo.add(Workspace(name=data.name, owner_id=owner.id))
        await self.repo.add_member(
            WorkspaceMember(workspace_id=workspace.id, user_id=owner.id, role=WorkspaceRole.OWNER)
        )
        return workspace
