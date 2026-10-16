from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.schemas.label import LabelResponse, LabelUpdate
from app.services.label import LabelService

router = APIRouter(prefix="/labels", tags=["Labels"])


@router.patch("/{label_id}", response_model=LabelResponse)
async def update_label(
    label_id: UUID, data: LabelUpdate, user: CurrentUser, db: DbSession
) -> LabelResponse:
    return LabelResponse.model_validate(await LabelService(db).update(label_id, data, user))


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(label_id: UUID, user: CurrentUser, db: DbSession) -> None:
    await LabelService(db).delete(label_id, user)
