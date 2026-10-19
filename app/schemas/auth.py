from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field

from app.schemas.common import check_password_bytes


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=100)
    password: Annotated[
        str, Field(min_length=8, max_length=128), AfterValidator(check_password_bytes)
    ]


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str
