from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class CommentResponse(ORMModel):
    id: UUID
    task_id: UUID
    author_id: UUID
    content: str
    created_at: datetime
