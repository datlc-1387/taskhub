from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.label import LabelCreate, LabelResponse
from app.schemas.project import ProjectResponse, ProjectUpdate
from app.services.label import LabelService
from app.services.project import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, user: CurrentUser, db: DbSession) -> ProjectResponse:
    return ProjectResponse.model_validate(await ProjectService(db).get(project_id, user))


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID, data: ProjectUpdate, user: CurrentUser, db: DbSession
) -> ProjectResponse:
    return ProjectResponse.model_validate(await ProjectService(db).update(project_id, data, user))


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: UUID, user: CurrentUser, db: DbSession) -> None:
    await ProjectService(db).delete(project_id, user)


@router.get("/{project_id}/labels", response_model=list[LabelResponse])
async def list_labels(project_id: UUID, user: CurrentUser, db: DbSession) -> list[LabelResponse]:
    items = await LabelService(db).list_in_project(project_id, user)
    return [LabelResponse.model_validate(label) for label in items]


@router.post(
    "/{project_id}/labels", response_model=LabelResponse, status_code=status.HTTP_201_CREATED
)
async def create_label(
    project_id: UUID, data: LabelCreate, user: CurrentUser, db: DbSession
) -> LabelResponse:
    return LabelResponse.model_validate(await LabelService(db).create(project_id, data, user))
