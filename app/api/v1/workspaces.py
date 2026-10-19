from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.project import ProjectCreate, ProjectResponse
from app.schemas.workspace import (
    MemberAdd,
    MemberResponse,
    MemberUpdate,
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.project import ProjectService
from app.services.workspace import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate, user: CurrentUser, db: DbSession
) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(await WorkspaceService(db).create(data, user))


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(user: CurrentUser, db: DbSession) -> list[WorkspaceResponse]:
    items = await WorkspaceService(db).list_mine(user)
    return [WorkspaceResponse.model_validate(w) for w in items]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: UUID, user: CurrentUser, db: DbSession) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(
        await WorkspaceService(db).get_workspace(workspace_id, user)
    )


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID, data: WorkspaceUpdate, user: CurrentUser, db: DbSession
) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(
        await WorkspaceService(db).update(workspace_id, data, user)
    )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(workspace_id: UUID, user: CurrentUser, db: DbSession) -> None:
    await WorkspaceService(db).delete(workspace_id, user)


@router.get("/{workspace_id}/members", response_model=list[MemberResponse])
async def list_members(
    workspace_id: UUID, user: CurrentUser, db: DbSession
) -> list[MemberResponse]:
    return await WorkspaceService(db).list_members(workspace_id, user)


@router.post(
    "/{workspace_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED
)
async def add_member(
    workspace_id: UUID, data: MemberAdd, user: CurrentUser, db: DbSession
) -> MemberResponse:
    return await WorkspaceService(db).add_member(workspace_id, data, user)


@router.patch("/{workspace_id}/members/{member_id}", response_model=MemberResponse)
async def update_member(
    workspace_id: UUID, member_id: UUID, data: MemberUpdate, user: CurrentUser, db: DbSession
) -> MemberResponse:
    return await WorkspaceService(db).update_member(workspace_id, member_id, data, user)


@router.delete("/{workspace_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    workspace_id: UUID, member_id: UUID, user: CurrentUser, db: DbSession
) -> None:
    await WorkspaceService(db).remove_member(workspace_id, member_id, user)


@router.get("/{workspace_id}/projects", response_model=list[ProjectResponse])
async def list_projects(
    workspace_id: UUID, user: CurrentUser, db: DbSession
) -> list[ProjectResponse]:
    items = await ProjectService(db).list_in_workspace(workspace_id, user)
    return [ProjectResponse.model_validate(p) for p in items]


@router.post(
    "/{workspace_id}/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED
)
async def create_project(
    workspace_id: UUID, data: ProjectCreate, user: CurrentUser, db: DbSession
) -> ProjectResponse:
    return ProjectResponse.model_validate(await ProjectService(db).create(workspace_id, data, user))
