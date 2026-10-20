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


@router.post(
    "",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a workspace (the caller becomes its OWNER)",
)
async def create_workspace(
    data: WorkspaceCreate, user: CurrentUser, db: DbSession
) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(await WorkspaceService(db).create(data, user))


@router.get(
    "",
    response_model=list[WorkspaceResponse],
    summary="List the workspaces the current user belongs to",
)
async def list_workspaces(user: CurrentUser, db: DbSession) -> list[WorkspaceResponse]:
    items = await WorkspaceService(db).list_mine(user)
    return [WorkspaceResponse.model_validate(w) for w in items]


@router.get("/{workspace_id}", response_model=WorkspaceResponse, summary="Get a workspace")
async def get_workspace(workspace_id: UUID, user: CurrentUser, db: DbSession) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(
        await WorkspaceService(db).get_workspace(workspace_id, user)
    )


@router.patch(
    "/{workspace_id}", response_model=WorkspaceResponse, summary="Rename a workspace (OWNER)"
)
async def update_workspace(
    workspace_id: UUID, data: WorkspaceUpdate, user: CurrentUser, db: DbSession
) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(
        await WorkspaceService(db).update(workspace_id, data, user)
    )


@router.delete(
    "/{workspace_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a workspace with all its projects and tasks (OWNER)",
)
async def delete_workspace(workspace_id: UUID, user: CurrentUser, db: DbSession) -> None:
    await WorkspaceService(db).delete(workspace_id, user)


@router.get(
    "/{workspace_id}/members",
    response_model=list[MemberResponse],
    summary="List the members of a workspace with their roles",
)
async def list_members(
    workspace_id: UUID, user: CurrentUser, db: DbSession
) -> list[MemberResponse]:
    return await WorkspaceService(db).list_members(workspace_id, user)


@router.post(
    "/{workspace_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a member as EDITOR or VIEWER (OWNER)",
)
async def add_member(
    workspace_id: UUID, data: MemberAdd, user: CurrentUser, db: DbSession
) -> MemberResponse:
    return await WorkspaceService(db).add_member(workspace_id, data, user)


@router.patch(
    "/{workspace_id}/members/{member_id}",
    response_model=MemberResponse,
    summary="Change a member's role to EDITOR or VIEWER (OWNER)",
)
async def update_member(
    workspace_id: UUID, member_id: UUID, data: MemberUpdate, user: CurrentUser, db: DbSession
) -> MemberResponse:
    return await WorkspaceService(db).update_member(workspace_id, member_id, data, user)


@router.delete(
    "/{workspace_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member; the workspace owner cannot be removed (OWNER)",
)
async def remove_member(
    workspace_id: UUID, member_id: UUID, user: CurrentUser, db: DbSession
) -> None:
    await WorkspaceService(db).remove_member(workspace_id, member_id, user)


@router.get(
    "/{workspace_id}/projects",
    response_model=list[ProjectResponse],
    summary="List the projects of a workspace",
)
async def list_projects(
    workspace_id: UUID, user: CurrentUser, db: DbSession
) -> list[ProjectResponse]:
    items = await ProjectService(db).list_in_workspace(workspace_id, user)
    return [ProjectResponse.model_validate(p) for p in items]


@router.post(
    "/{workspace_id}/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project in a workspace (EDITOR or higher)",
)
async def create_project(
    workspace_id: UUID, data: ProjectCreate, user: CurrentUser, db: DbSession
) -> ProjectResponse:
    return ProjectResponse.model_validate(await ProjectService(db).create(workspace_id, data, user))
