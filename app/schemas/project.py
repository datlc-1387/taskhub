from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import ProjectStatus
from app.schemas.common import ORMModel


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)


class ProjectResponse(ORMModel):
    id: UUID
    workspace_id: UUID
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime
