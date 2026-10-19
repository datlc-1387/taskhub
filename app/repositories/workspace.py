from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import User, Workspace, WorkspaceMember
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

    async def remove_member(self, member: WorkspaceMember) -> None:
        await self.db.delete(member)
        await self.db.flush()

    async def list_members(self, workspace_id: UUID) -> Sequence[WorkspaceMember]:
        stmt = (
            select(WorkspaceMember)
            .options(joinedload(WorkspaceMember.user))
            .where(WorkspaceMember.workspace_id == workspace_id)
            .order_by(WorkspaceMember.role, WorkspaceMember.user_id)
        )
        return (await self.db.scalars(stmt)).all()

    async def get_user(self, user_id: UUID) -> User | None:
        return await self.db.get(User, user_id)
