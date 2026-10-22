from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, status

from app.api.deps import Cache, CurrentUser, DbSession, PageParams, TaskFilterParams
from app.api.responses import PROJECT_ARCHIVED
from app.schemas.common import Page
from app.schemas.label import LabelCreate, LabelResponse
from app.schemas.project import ProjectResponse, ProjectUpdate
from app.schemas.task import TaskCreate, TaskResponse
from app.services.label import LabelService
from app.services.project import ProjectService
from app.services.task import TaskService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/{project_id}", response_model=ProjectResponse, summary="Get a project")
async def get_project(project_id: UUID, user: CurrentUser, db: DbSession) -> ProjectResponse:
    return ProjectResponse.model_validate(await ProjectService(db).get(project_id, user))


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update the name or description of a project (EDITOR)",
)
async def update_project(
    project_id: UUID, data: ProjectUpdate, user: CurrentUser, db: DbSession
) -> ProjectResponse:
    return ProjectResponse.model_validate(await ProjectService(db).update(project_id, data, user))


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project with its tasks and labels (OWNER)",
)
async def delete_project(project_id: UUID, user: CurrentUser, db: DbSession) -> None:
    await ProjectService(db).delete(project_id, user)


@router.post(
    "/{project_id}/archive",
    response_model=ProjectResponse,
    summary="Archive a project: its tasks, labels and comments become read-only (EDITOR)",
)
async def archive_project(project_id: UUID, user: CurrentUser, db: DbSession) -> ProjectResponse:
    return ProjectResponse.model_validate(await ProjectService(db).archive(project_id, user))


@router.get(
    "/{project_id}/tasks",
    response_model=Page[TaskResponse],
    summary="List tasks with status/priority/assignee filters and pagination (cached)",
)
async def list_tasks(
    project_id: UUID,
    filters: TaskFilterParams,
    page: PageParams,
    user: CurrentUser,
    db: DbSession,
    cache: Cache,
) -> Page[TaskResponse]:
    return await TaskService(db, cache).list_in_project(project_id, filters, page, user)


@router.post(
    "/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task, optionally assigned and labeled (EDITOR)",
    responses=PROJECT_ARCHIVED,
)
async def create_task(
    project_id: UUID,
    data: TaskCreate,
    background: BackgroundTasks,
    user: CurrentUser,
    db: DbSession,
    cache: Cache,
) -> TaskResponse:
    return TaskResponse.model_validate(
        await TaskService(db, cache).create(project_id, data, user, background)
    )


@router.get(
    "/{project_id}/labels",
    response_model=list[LabelResponse],
    summary="List the labels of a project",
)
async def list_labels(
    project_id: UUID, user: CurrentUser, db: DbSession, cache: Cache
) -> list[LabelResponse]:
    items = await LabelService(db, cache).list_in_project(project_id, user)
    return [LabelResponse.model_validate(label) for label in items]


@router.post(
    "/{project_id}/labels",
    response_model=LabelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a label in a project (EDITOR)",
    responses=PROJECT_ARCHIVED,
)
async def create_label(
    project_id: UUID, data: LabelCreate, user: CurrentUser, db: DbSession, cache: Cache
) -> LabelResponse:
    return LabelResponse.model_validate(
        await LabelService(db, cache).create(project_id, data, user)
    )
