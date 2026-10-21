from typing import Any

from app.schemas.common import ErrorResponse

Responses = dict[int | str, dict[str, Any]]


def error_response(status_code: int, description: str) -> Responses:
    return {status_code: {"model": ErrorResponse, "description": description}}


PROJECT_ARCHIVED = error_response(409, "The project is archived (read-only)")
LABEL_CONFLICT = error_response(
    409, "The label is already attached to the task, or the project is archived"
)
