from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


def create_engine(url: str, echo: bool = False) -> AsyncEngine:
    kwargs: dict[str, object] = {"echo": echo}
    if not url.startswith("sqlite"):
        kwargs.update(pool_size=20, max_overflow=10, pool_pre_ping=True)
    return create_async_engine(url, **kwargs)


settings = get_settings()
engine = create_engine(settings.database_url, settings.db_echo)
