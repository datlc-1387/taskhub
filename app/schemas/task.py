from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import TASK_DESCRIPTION_MAX_LENGTH, TASK_TITLE_MAX_LENGTH
from app.models.enums import TaskPriority, TaskStatus
from app.schemas.common import ORMModel
from app.schemas.label import LabelResponse


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=TASK_TITLE_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=TASK_DESCRIPTION_MAX_LENGTH)
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None
    assignee_id: UUID | None = None
    label_ids: list[UUID] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=TASK_TITLE_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=TASK_DESCRIPTION_MAX_LENGTH)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    assignee_id: UUID | None = None


class TaskResponse(ORMModel):
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    due_date: datetime | None
    assignee_id: UUID | None
    created_by: UUID
    created_at: datetime
    labels: list[LabelResponse]
