from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, EmailStr, Field

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
    full_name: str | None = Field(default=None, min_length=1, max_length=100)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: Annotated[
        str, Field(min_length=8, max_length=128), AfterValidator(check_password_bytes)
    ]
