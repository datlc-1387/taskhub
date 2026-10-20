from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field

from app.core.constants import FULL_NAME_MAX_LENGTH, PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH
from app.schemas.common import check_password_bytes


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=FULL_NAME_MAX_LENGTH)
    password: Annotated[
        str,
        Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH),
        AfterValidator(check_password_bytes),
    ]


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str
