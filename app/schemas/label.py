from uuid import UUID

from pydantic import BaseModel, Field

from app.core.constants import LABEL_NAME_MAX_LENGTH
from app.schemas.common import ORMModel

HEX_COLOR = r"^#[0-9a-fA-F]{6}$"


class LabelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=LABEL_NAME_MAX_LENGTH)
    color: str = Field(default="#808080", pattern=HEX_COLOR)


class LabelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=LABEL_NAME_MAX_LENGTH)
    color: str | None = Field(default=None, pattern=HEX_COLOR)


class LabelResponse(ORMModel):
    id: UUID
    project_id: UUID
    name: str
    color: str
