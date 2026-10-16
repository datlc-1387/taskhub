from fastapi import APIRouter

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.get("")
async def demo():
    return "demo"
