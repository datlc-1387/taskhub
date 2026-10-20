from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, EmailStr, Field

from app.core.constants import FULL_NAME_MAX_LENGTH, PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH
from app.models.enums import UserRole
from app.schemas.common import ORMModel, check_password_bytes


class UserResponse(ORMModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=FULL_NAME_MAX_LENGTH)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: Annotated[
        str,
        Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH),
        AfterValidator(check_password_bytes),
    ]
