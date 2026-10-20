from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.core import messages
from app.core.constants import PASSWORD_MAX_LENGTH


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
    if len(value.encode("utf-8")) > PASSWORD_MAX_LENGTH:
        raise ValueError(messages.PASSWORD_TOO_LONG.format(max_bytes=PASSWORD_MAX_LENGTH))

    return value


@dataclass(frozen=True)
class Pagination:
    page: int
    limit: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit
