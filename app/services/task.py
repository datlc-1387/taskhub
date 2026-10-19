from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.models import Label, Task, User, UserRole, WorkspaceRole
from app.repositories.label import LabelRepository
from app.repositories.task import TaskRepository
from app.repositories.workspace import WorkspaceRepository
from app.schemas.common import Page, Pagination, TaskFilter
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.permissions import PermissionService


class TaskService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = TaskRepository(db)
        self.perms = PermissionService(db)
        self.workspaces = WorkspaceRepository(db)
        self.labels = LabelRepository(db)

    async def list_in_project(
        self, project_id: UUID, filters: TaskFilter, page: Pagination, user: User
    ) -> Page[TaskResponse]:
        await self.perms.require_project(project_id, user)
        items, total = await self.repo.list_by_project(project_id, filters, page)
        result = Page[TaskResponse](
            items=[TaskResponse.model_validate(t) for t in items],
            total=total,
            page=page.page,
            limit=page.limit,
        )
        return result

    async def create(self, project_id: UUID, data: TaskCreate, user: User) -> Task:
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
        return task

    async def get(self, task_id: UUID, user: User) -> Task:
        return await self.perms.require_task(task_id, user)

    async def update(self, task_id: UUID, data: TaskUpdate, user: User) -> Task:
        task = await self.perms.require_task(task_id, user, WorkspaceRole.EDITOR)
        changes = data.model_dump(exclude_unset=True)
        new_assignee = changes.get("assignee_id")
        assignee_changed = "assignee_id" in changes and new_assignee != task.assignee_id
        if assignee_changed and new_assignee is not None:
            await self._ensure_member(task.project.workspace_id, new_assignee)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(task, field, value)
        await self.db.flush()
        return task

    async def delete(self, task_id: UUID, user: User) -> None:
        task = await self.perms.require_task(task_id, user)
        role = await self.perms.role_in_workspace(task.project.workspace_id, user)
        is_editor = role in (WorkspaceRole.OWNER, WorkspaceRole.EDITOR)
        is_privileged = is_editor or user.role == UserRole.ADMIN
        if not is_privileged and task.created_by != user.id:
            raise ForbiddenError("Only EDITOR/OWNER or the creator can delete the task")
        await self.repo.delete(task)

    async def add_label(self, task_id: UUID, label_id: UUID, user: User) -> Task:
        task = await self.perms.require_task(task_id, user, WorkspaceRole.EDITOR)
        label = await self._label_in_project(label_id, task.project_id)
        if label not in task.labels:
            task.labels.append(label)
            await self.db.flush()
        return task

    async def remove_label(self, task_id: UUID, label_id: UUID, user: User) -> Task:
        task = await self.perms.require_task(task_id, user, WorkspaceRole.EDITOR)
        label = await self._label_in_project(label_id, task.project_id)
        if label in task.labels:
            task.labels.remove(label)
            await self.db.flush()
        return task

    async def _ensure_member(self, workspace_id: UUID, user_id: UUID) -> None:
        if await self.workspaces.get_member(workspace_id, user_id) is None:
            raise NotFoundError(f"User {user_id} is not a member of the workspace")

    async def _labels_in_project(self, label_ids: list[UUID], project_id: UUID) -> list[Label]:
        labels = list(await self.labels.get_many_in_project(label_ids, project_id))
        missing = set(label_ids) - {label.id for label in labels}
        if missing:
            raise NotFoundError(
                f"Label {', '.join(str(x) for x in sorted(missing))} do not belong to the project"
            )
        return labels

    async def _label_in_project(self, label_id: UUID, project_id: UUID) -> Label:
        label = await self.labels.get(label_id)
        if label is None or label.project_id != project_id:
            raise NotFoundError(f"Label {label_id} does not belong to the project")
        return label
