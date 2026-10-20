from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DbSession
from app.schemas.auth import RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.common import ErrorResponse
from app.schemas.user import UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse, "description": "Email already exists"}},
)
async def register(data: RegisterRequest, db: DbSession) -> UserResponse:
    return UserResponse.model_validate(await AuthService(db).register(data))


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse, "description": "Incorrect email or password"}},
    summary="Login (OAuth2 password flow, send form-data)",
)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession
) -> TokenResponse:
    return TokenResponse.model_validate(
        await AuthService(db).login(email=form.username, password=form.password)
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse, "description": "Refresh token invalid or revoked"}},
)
async def refresh(data: RefreshRequest, db: DbSession) -> TokenResponse:
    return TokenResponse.model_validate(await AuthService(db).refresh(data.refresh_token))


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"model": ErrorResponse, "description": "Refresh token invalid or revoked"}},
)
async def logout(data: RefreshRequest, db: DbSession) -> None:
    await AuthService(db).logout(data.refresh_token)
