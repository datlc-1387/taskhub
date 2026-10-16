from fastapi import APIRouter

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("")
async def demo() -> str:
    return "demo"
