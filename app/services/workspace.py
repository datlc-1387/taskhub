from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models import User, Workspace, WorkspaceMember, WorkspaceRole
from app.repositories.user import UserRepository
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
        self.users = UserRepository(db)
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
        return [self._to_member_response(member) for member in items]

    async def add_member(self, workspace_id: UUID, data: MemberAdd, user: User) -> MemberResponse:
        await self.perms.require_workspace(workspace_id, user, WorkspaceRole.OWNER)
        target = await self.users.get(data.user_id)
        if target is None:
            raise NotFoundError(messages.USER_NOT_FOUND.format(user_id=data.user_id))
        if await self.repo.get_member(workspace_id, data.user_id) is not None:
            raise ConflictError(messages.USER_ALREADY_MEMBER)
        try:
            member = await self.repo.add_member(
                WorkspaceMember(
                    workspace_id=workspace_id, user_id=data.user_id, role=data.role, user=target
                )
            )
        except IntegrityError as exc:
            raise ConflictError(messages.USER_ALREADY_MEMBER) from exc
        return self._to_member_response(member)

    async def update_member(
        self, workspace_id: UUID, member_id: UUID, data: MemberUpdate, user: User
    ) -> MemberResponse:
        workspace = await self.perms.require_workspace(workspace_id, user, WorkspaceRole.OWNER)
        member = await self._get_member(workspace, member_id=member_id)
        if member.user_id == workspace.owner_id:
            raise ForbiddenError(messages.CANNOT_CHANGE_OWNER_ROLE)
        member.role = data.role
        await self.db.flush()
        return self._to_member_response(member)

    async def remove_member(self, workspace_id: UUID, member_id: UUID, user: User) -> None:
        workspace = await self.perms.require_workspace(workspace_id, user, WorkspaceRole.OWNER)
        member = await self._get_member(workspace, member_id)
        if member.user_id == workspace.owner_id:
            raise ForbiddenError(messages.CANNOT_CHANGE_WORKSPACE_OWNER)
        await self.repo.remove_member(member)

    async def list_mine(self, user: User) -> list[Workspace]:
        return list(await self.repo.list_for_user(user.id))

    async def get_workspace(self, workspace_id: UUID, user: User) -> Workspace:
        return await self.perms.require_workspace(workspace_id, user)

    async def _get_member(self, workspace: Workspace, member_id: UUID) -> WorkspaceMember:
        member = await self.repo.get_member_with_user(workspace_id=workspace.id, user_id=member_id)
        if member is None:
            raise NotFoundError(messages.USER_NOT_MEMBER.format(user_id=member_id))
        return member

    @staticmethod
    def _to_member_response(member: WorkspaceMember) -> MemberResponse:
        return MemberResponse(
            user_id=member.user_id,
            email=member.user.email,
            full_name=member.user.full_name,
            role=member.role,
        )
