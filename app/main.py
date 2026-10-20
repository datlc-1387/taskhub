from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.openapi import install_error_responses
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
            "Task Management API — demo project cho FastAPI.\n\n"
            "Log in via `POST /api/v1/auth/login` (form-data), then click **Authorize** "
            "to test APIs that require a token."
        ),
        version="1.0.0",
        lifespan=lifespan,
        openapi_tags=[
            {"name": "System", "description": "Health check"},
            {
                "name": "Auth",
                "description": "Register, Login, refresh/logout using JWT",
            },
            {"name": "Users", "description": "Personal Profile"},
            {
                "name": "Workspaces",
                "description": "Workspaces, members, and the projects within them",
            },
            {
                "name": "Projects",
                "description": "Project, Task list (filter, pagination, cache), Label",
            },
            {
                "name": "Tasks",
                "description": "Detailed tasks, assigning labels, and adding comments",
            },
            {"name": "Labels", "description": "Update/Delete label"},
        ],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    install_error_responses(app)

    @app.get("/health", tags=["System"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "version": app.version}

    return app


app = create_app()
