from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse
from app.services.workspace import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate, user: CurrentUser, db: DbSession
) -> WorkspaceResponse:
    return WorkspaceResponse.model_validate(await WorkspaceService(db).create(data, user))
