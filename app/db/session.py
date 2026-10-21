from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


def create_engine(
    url: str, echo: bool = False, pool_size: int = 5, max_overflow: int = 5
) -> AsyncEngine:
    kwargs: dict[str, object] = {"echo": echo}
    if not url.startswith("sqlite"):
        kwargs.update(pool_size=pool_size, max_overflow=max_overflow, pool_pre_ping=True)
    return create_async_engine(url, **kwargs)


settings = get_settings()
engine = create_engine(
    settings.database_url, settings.db_echo, settings.db_pool_size, settings.db_max_overflow
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
