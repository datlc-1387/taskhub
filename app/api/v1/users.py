from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.user import ChangePasswordRequest, UserResponse, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def read_me(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_me(data: UserUpdate, user: CurrentUser, db: DbSession) -> UserResponse:
    return UserResponse.model_validate(await UserService(db).update_profile(user, data))


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(data: ChangePasswordRequest, user: CurrentUser, db: DbSession) -> None:
    await UserService(db).change_password(user, data)
