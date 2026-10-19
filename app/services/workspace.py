from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models import User, Workspace, WorkspaceMember, WorkspaceRole
from app.repositories.workspace import WorkspaceRepository
from app.schemas.workspace import (
    MemberAdd,
    MemberResponse,
    MemberUpdate,
    WorkspaceCreate,
    WorkspaceUpdate,
)
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

    async def list_members(self, workspace_id: UUID, user: User) -> list[MemberResponse]:
        await self.perms.require_workspace(workspace_id, user)
        items = await self.repo.list_members(workspace_id)
        return [
            MemberResponse(
                user_id=member.user_id,
                email=member.user.email,
                full_name=member.user.full_name,
                role=member.role,
            )
            for member in items
        ]

    async def add_member(self, workspace_id: UUID, data: MemberAdd, user: User) -> MemberResponse:
        await self.perms.require_workspace(workspace_id, user, WorkspaceRole.OWNER)
        if data.role == WorkspaceRole.OWNER:
            raise ForbiddenError("Cannot grant OWNER role to another member")
        target = await self.repo.get_user(data.user_id)
        if target is None:
            raise NotFoundError(f"User {data.user_id} doesn't exist")
        if await self.repo.get_member(workspace_id, data.user_id) is not None:
            raise ConflictError("The user is already a member of the workspace")
        member = await self.repo.add_member(
            WorkspaceMember(workspace_id=workspace_id, user_id=data.user_id, role=data.role)
        )
        return MemberResponse(
            user_id=member.user_id,
            email=target.email,
            full_name=target.full_name,
            role=member.role,
        )

    async def update_member(
        self, workspace_id: UUID, member_id: UUID, data: MemberUpdate, user: User
    ) -> MemberResponse:
        workspace = await self.perms.require_workspace(workspace_id, user, WorkspaceRole.OWNER)
        member = await self._get_member_or_404(workspace, member_id=member_id)
        if data.role == WorkspaceRole.OWNER or member.user_id == workspace.owner_id:
            raise ForbiddenError("Cannot change OWNER role")
        member.role = data.role
        await self.db.flush()
        target = await self.repo.get_user(member_id)
        assert target is not None
        return MemberResponse(
            user_id=member.user_id,
            email=target.email,
            full_name=target.full_name,
            role=member.role,
        )

    async def remove_member(self, workspace_id: UUID, member_id: UUID, user: User) -> None:
        workspace = await self.perms.require_workspace(workspace_id, user, WorkspaceRole.OWNER)
        member = await self._get_member_or_404(workspace, member_id)
        if member.user_id == workspace.owner_id:
            raise ForbiddenError("Cannot change or remove the workspace owner")
        await self.repo.remove_member(member)

    async def list_mine(self, user: User) -> list[Workspace]:
        return list(await self.repo.list_for_user(user.id))

    async def get_workspace(self, workspace_id: UUID, user: User) -> Workspace:
        return await self.perms.require_workspace(workspace_id, user)

    async def _get_member_or_404(self, workspace: Workspace, member_id: UUID) -> WorkspaceMember:
        member = await self.repo.get_member(workspace_id=workspace.id, user_id=member_id)
        if member is None:
            raise NotFoundError(f"The user {member_id} does not belong to the workspace")
        return member
