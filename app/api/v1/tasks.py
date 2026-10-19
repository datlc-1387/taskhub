from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.comment import CommentCreate, CommentResponse
from app.schemas.task import TaskResponse, TaskUpdate
from app.services.comment import CommentService
from app.services.task import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID, user: CurrentUser, db: DbSession) -> TaskResponse:
    return TaskResponse.model_validate(await TaskService(db).get(task_id, user))


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID, data: TaskUpdate, background: BackgroundTasks, user: CurrentUser, db: DbSession
) -> TaskResponse:
    return TaskResponse.model_validate(
        await TaskService(db).update(task_id, data, user, background)
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: UUID, user: CurrentUser, db: DbSession) -> None:
    await TaskService(db).delete(task_id, user)


@router.post("/{task_id}/labels/{label_id}", response_model=TaskResponse)
async def add_label(
    task_id: UUID, label_id: UUID, user: CurrentUser, db: DbSession
) -> TaskResponse:
    return TaskResponse.model_validate(await TaskService(db).add_label(task_id, label_id, user))


@router.delete("/{task_id}/labels/{label_id}", response_model=TaskResponse)
async def remove_label(
    task_id: UUID, label_id: UUID, user: CurrentUser, db: DbSession
) -> TaskResponse:
    return TaskResponse.model_validate(await TaskService(db).remove_label(task_id, label_id, user))


@router.get("/{task_id}/comments", response_model=list[CommentResponse])
async def get_comments(task_id: UUID, user: CurrentUser, db: DbSession) -> list[CommentResponse]:
    items = await CommentService(db).list_for_task(task_id, user)
    return [CommentResponse.model_validate(comment) for comment in items]


@router.post(
    "/{task_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED
)
async def add_comment(
    task_id: UUID, data: CommentCreate, user: CurrentUser, db: DbSession
) -> CommentResponse:
    return CommentResponse.model_validate(await CommentService(db).add(task_id, data, user))


@router.delete("/{task_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(task_id: UUID, comment_id: UUID, user: CurrentUser, db: DbSession) -> None:
    await CommentService(db).delete(task_id, comment_id, user)
