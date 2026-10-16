from fastapi import APIRouter

from app.api.v1 import labels, projects, tasks, users, workspaces

api_router = APIRouter()
api_router.include_router(labels.router)
api_router.include_router(tasks.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(workspaces.router)
