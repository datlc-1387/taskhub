from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import CacheBackend
from app.core.exceptions import NotFoundError
from app.models import Label, User, WorkspaceRole
from app.repositories.label import LabelRepository
from app.schemas.label import LabelCreate, LabelUpdate
from app.services.permissions import PermissionService
from app.services.task import tasks_cache_prefix


class LabelService:
    def __init__(self, db: AsyncSession, cache: CacheBackend) -> None:
        self.db = db
        self.cache = cache
        self.repo = LabelRepository(db)
        self.perms = PermissionService(db)

    async def list_in_project(self, project_id: UUID, user: User) -> list[Label]:
        await self.perms.require_project(project_id, user)
        return list(await self.repo.list_by_project(project_id))

    async def create(self, project_id: UUID, data: LabelCreate, user: User) -> Label:
        await self.perms.require_project(project_id, user, WorkspaceRole.EDITOR)
        return await self.repo.add(Label(project_id=project_id, **data.model_dump()))

    async def update(self, label_id: UUID, data: LabelUpdate, user: User) -> Label:
        label = await self._get(label_id, user)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(label, field, value)
        await self.db.flush()
        await self.cache.delete_prefix(tasks_cache_prefix(label.project_id))
        return label

    async def delete(self, label_id: UUID, user: User) -> None:
        label = await self._get(label_id, user)
        await self.repo.delete(label)
        await self.cache.delete_prefix(tasks_cache_prefix(label.project_id))

    async def _get(self, label_id: UUID, user: User) -> Label:
        label = await self.repo.get(label_id)
        if label is None:
            raise NotFoundError(f"Label {label_id} does not exist.")
        await self.perms.require_project(label.project_id, user, WorkspaceRole.EDITOR)
        return label
