from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("")
async def demo() -> str:
    return "demo"
