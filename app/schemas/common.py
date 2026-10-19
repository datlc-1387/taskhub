from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models import TaskPriority, TaskStatus


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    limit: int

    @property
    def pages(self) -> int:
        return (self.total + self.limit - 1) // self.limit if self.limit else 0


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def check_password_bytes(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError(
            "Maximum password length is 72 bytes (approximately 72 unaccented characters)"
        )

    return value


@dataclass(frozen=True)
class Pagination:
    page: int
    limit: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


@dataclass(frozen=True)
class TaskFilter:
    status: TaskStatus | None
    priority: TaskPriority | None
    assignee_id: UUID | None

    def cache_key(self) -> str:
        return f"{self.status or '-'}:{self.priority or '-'}:{self.assignee_id or '-'}"
