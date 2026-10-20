from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import WORKSPACE_NAME_MAX_LENGTH
from app.models import WorkspaceRole
from app.schemas.common import ORMModel


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=WORKSPACE_NAME_MAX_LENGTH)


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=WORKSPACE_NAME_MAX_LENGTH)


class WorkspaceResponse(ORMModel):
    id: UUID
    name: str
    owner_id: UUID
    created_at: datetime


class MemberAdd(BaseModel):
    user_id: UUID
    role: WorkspaceRole = WorkspaceRole.VIEWER


class MemberUpdate(BaseModel):
    role: WorkspaceRole


class MemberResponse(ORMModel):
    user_id: UUID
    email: str
    full_name: str
    role: WorkspaceRole
