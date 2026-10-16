from uuid import UUID

from fastapi import APIRouter

router = APIRouter(prefix="/labels", tags=["Labels"])


@router.patch("/{label_id}")
async def update_label(label_id: UUID) -> str:
    return "demo"
