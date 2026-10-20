from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import PROJECT_DESCRIPTION_MAX_LENGTH, PROJECT_NAME_MAX_LENGTH
from app.models.enums import ProjectStatus
from app.schemas.common import ORMModel


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=PROJECT_NAME_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=PROJECT_DESCRIPTION_MAX_LENGTH)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=PROJECT_NAME_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=PROJECT_DESCRIPTION_MAX_LENGTH)


class ProjectResponse(ORMModel):
    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime
