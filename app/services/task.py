from typing import Any
from uuid import UUID

from fastapi import BackgroundTasks
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import messages
from app.core.cache import CacheBackend
from app.core.config import get_settings
from app.core.exceptions import ConflictError, NotFoundError
from app.models import Label, Task, User, WorkspaceRole
from app.repositories.label import LabelRepository
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.common import Page, Pagination
from app.schemas.task import TaskCreate, TaskFilter, TaskResponse, TaskUpdate
from app.services.notifications import send_assignment_email
from app.services.permissions import PermissionService


def tasks_cache_prefix(project_id: UUID) -> str:
    return f"tasks:{project_id}:"


class TaskService:
    def __init__(self, db: AsyncSession, cache: CacheBackend) -> None:
        self.db = db
        self.cache = cache
        self.repo = TaskRepository(db)
        self.perms = PermissionService(db)
        self.workspaces = WorkspaceRepository(db)
        self.users = UserRepository(db)
        self.labels = LabelRepository(db)

    async def list_in_project(
        self, project_id: UUID, filters: TaskFilter, page: Pagination, user: User
    ) -> Page[TaskResponse]:
        await self.perms.require_project(project_id, user)
        key = f"{tasks_cache_prefix(project_id)}{filters.cache_key()}:{page.page}:{page.limit}"
        cached: dict[str, Any] | None = await self.cache.get(key)
        if cached is not None:
            return Page[TaskResponse].model_validate(cached)

        items, total = await self.repo.list_by_project(project_id, filters, page)
        result = Page[TaskResponse](
            items=[TaskResponse.model_validate(t) for t in items],
            total=total,
            page=page.page,
            limit=page.limit,
        )
        await self.cache.set(key, result.model_dump(mode="json"), get_settings().cache_ttl_seconds)
        return result

    async def create(
        self, project_id: UUID, data: TaskCreate, user: User, background: BackgroundTasks
    ) -> Task:
        project = await self.perms.require_project(project_id, user, WorkspaceRole.EDITOR)
        if data.assignee_id is not None:
            await self._ensure_member(project.workspace_id, data.assignee_id)
        labels = await self._labels_in_project(data.label_ids, project_id)
        task = Task(
            project_id=project_id,
            created_by=user.id,
            labels=labels,
            **data.model_dump(exclude={"label_ids"}),
        )
        task = await self.repo.add(task)
        await self.cache.delete_prefix(tasks_cache_prefix(project_id))
        if task.assignee_id is not None:
            await self._notify_assignee(task, user, background)
        return task

    async def get(self, task_id: UUID, user: User) -> Task:
        return await self.perms.require_task(task_id, user)

    async def update(
        self, task_id: UUID, data: TaskUpdate, user: User, background: BackgroundTasks
    ) -> Task:
        task = await self.perms.require_task(task_id, user, WorkspaceRole.EDITOR)
        changes = data.model_dump(exclude_unset=True)
        new_assignee = changes.get("assignee_id")
        assignee_changed = "assignee_id" in changes and new_assignee != task.assignee_id
        if assignee_changed and new_assignee is not None:
            await self._ensure_member(task.project.workspace_id, new_assignee)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(task, field, value)
        await self.db.flush()
        await self.cache.delete_prefix(tasks_cache_prefix(task.project_id))
        if assignee_changed and task.assignee_id is not None:
            await self._notify_assignee(task, user, background)
        return task

    async def delete(self, task_id: UUID, user: User) -> None:
        task, role = await self.perms.require_task_with_role(task_id, user)
        self.perms.require_author_or_role(
            user, task.created_by, role, WorkspaceRole.EDITOR, messages.TASK_DELETE_FORBIDDEN
        )
        await self.repo.delete(task)
        await self.cache.delete_prefix(tasks_cache_prefix(task.project_id))

    async def add_label(self, task_id: UUID, label_id: UUID, user: User) -> Task:
        task = await self.perms.require_task(task_id, user, WorkspaceRole.EDITOR)
        label = await self._label_in_project(label_id, task.project_id)
        if label in task.labels:
            raise ConflictError(messages.LABEL_ALREADY_ON_TASK.format(label_id=label_id))
        task.labels.append(label)
        try:
            await self.db.flush()
        except IntegrityError as exc:  # another request attached the same label meanwhile
            raise ConflictError(messages.LABEL_ALREADY_ON_TASK.format(label_id=label_id)) from exc
        await self.cache.delete_prefix(tasks_cache_prefix(task.project_id))
        return task

    async def remove_label(self, task_id: UUID, label_id: UUID, user: User) -> Task:
        task = await self.perms.require_task(task_id, user, WorkspaceRole.EDITOR)
        label = await self._label_in_project(label_id, task.project_id)
        if label not in task.labels:
            raise NotFoundError(messages.LABEL_NOT_ON_TASK.format(label_id=label_id))
        task.labels.remove(label)
        await self.db.flush()
        await self.cache.delete_prefix(tasks_cache_prefix(task.project_id))
        return task

    async def _ensure_member(self, workspace_id: UUID, user_id: UUID) -> None:
        if await self.workspaces.get_member(workspace_id, user_id) is None:
            raise NotFoundError(messages.USER_NOT_MEMBER.format(user_id=user_id))

    async def _labels_in_project(self, label_ids: list[UUID], project_id: UUID) -> list[Label]:
        labels = list(await self.labels.get_many_in_project(label_ids, project_id))
        missing = set(label_ids) - {label.id for label in labels}
        if missing:
            missing_ids = ", ".join(str(x) for x in sorted(missing))
            raise NotFoundError(messages.LABELS_NOT_IN_PROJECT.format(label_ids=missing_ids))
        return labels

    async def _label_in_project(self, label_id: UUID, project_id: UUID) -> Label:
        label = await self.labels.get(label_id)
        if label is None or label.project_id != project_id:
            raise NotFoundError(messages.LABEL_NOT_IN_PROJECT.format(label_id=label_id))
        return label

    async def _notify_assignee(self, task: Task, actor: User, background: BackgroundTasks) -> None:
        assert task.assignee_id is not None
        assignee = await self.users.get(task.assignee_id)
        if assignee is not None:
            background.add_task(send_assignment_email, assignee.email, task.title, actor.full_name)
