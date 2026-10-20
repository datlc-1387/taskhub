import os

os.environ["MAIL_ENABLED"] = "false"
os.environ["DB_ECHO"] = "false"
os.environ.setdefault("SECRET_KEY", "test-secret-key-only-for-pytest-0123456789")

from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.core.cache import InMemoryCache, get_cache
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(
        "sqlite+aiosqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    cache = InMemoryCache()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_cache] = lambda: cache
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


async def register_and_login(
    client: AsyncClient, email: str, password: str = "secret123"
) -> dict[str, str]:
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": email.split("@")[0].title(), "password": password},
    )
    assert res.status_code == 201, res.text
    res = await client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest_asyncio.fixture
async def owner(client: AsyncClient) -> dict[str, str]:
    return await register_and_login(client, "owner@example.com")


@pytest_asyncio.fixture
async def member(client: AsyncClient) -> dict[str, str]:
    return await register_and_login(client, "member@example.com")


@pytest_asyncio.fixture
async def workspace(client: AsyncClient, owner: dict[str, str]) -> str:
    res = await client.post("/api/v1/workspaces", json={"name": "Sun* Team"}, headers=owner)
    assert res.status_code == 201, res.text
    return str(res.json()["id"])


@pytest_asyncio.fixture
async def project(client: AsyncClient, owner: dict[str, str], workspace: str) -> str:
    res = await client.post(
        f"/api/v1/workspaces/{workspace}/projects",
        json={"name": "TaskHub API", "description": "Demo"},
        headers=owner,
    )
    assert res.status_code == 201, res.text
    return str(res.json()["id"])


async def user_id_of(client: AsyncClient, headers: dict[str, str]) -> str:
    res = await client.get("/api/v1/users/me", headers=headers)
    return str(res.json()["id"])
