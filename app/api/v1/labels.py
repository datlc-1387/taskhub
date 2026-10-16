from fastapi import APIRouter

router = APIRouter(prefix="/labels", tags=["Labels"])


@router.get("")
async def demo():
    return "demo"
