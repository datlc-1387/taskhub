from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class WorkspaceResponse(ORMModel):
    id: UUID
    name: str
    owner_id: UUID
    created_at: datetime
