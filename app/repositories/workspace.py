from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select

from app.models import Workspace, WorkspaceMember
from app.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[Workspace]):
    model = Workspace

    async def list_for_user(self, user_id: UUID) -> Sequence[Workspace]:
        stmt = (
            select(Workspace)
            .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
            .where(WorkspaceMember.user_id == user_id)
            .order_by(Workspace.created_at)
        )
        return (await self.db.scalars(stmt)).all()

    async def add_member(self, member: WorkspaceMember) -> WorkspaceMember:
        self.db.add(member)
        await self.db.flush()
        return member

    async def get_member(self, workspace_id: UUID, user_id: UUID) -> WorkspaceMember | None:
        return await self.db.get(WorkspaceMember, (workspace_id, user_id))
