from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.db.session import engine

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        setup_logging(settings.debug)
        yield
    finally:
        await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description=(
            "Task Management API — demo project cho khóa FastAPI (Sun* Python tech stack).\n\n"
            "Đăng nhập tại `POST /api/v1/auth/login` (form-data) rồi bấm **Authorize** "
            "để thử các API cần token."
        ),
        version="1.0.0",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "System", "description": "Health check"},
            {
                "name": "Auth",
                "description": "Đăng ký, đăng nhập, refresh/logout bằng JWT",
            },
            {"name": "Users", "description": "Hồ sơ cá nhân"},
            {
                "name": "Workspaces",
                "description": "Workspace, thành viên và project bên trong",
            },
            {
                "name": "Projects",
                "description": "Project, task list (filter, phân trang, cache), label",
            },
            {"name": "Tasks", "description": "Task chi tiết, gán label, comment"},
            {"name": "Labels", "description": "Sửa/xóa label"},
        ],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["System"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "version": app.version}

    return app


app = create_app()
