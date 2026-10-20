from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core import messages
from app.models import User
from tests.conftest import register_and_login


async def test_register_returns_public_fields_only(client: AsyncClient) -> None:
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "full_name": "Alice", "password": "secret123"},
    )
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "alice@example.com"
    assert body["role"] == "MEMBER"
    assert "hashed_password" not in body and "password" not in body


async def test_register_duplicate_email_is_409(client: AsyncClient) -> None:
    payload = {"email": "dup@example.com", "full_name": "Dup", "password": "secret123"}
    assert (await client.post("/api/v1/auth/register", json=payload)).status_code == 201
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "conflict"


async def test_register_validation_error_format(client: AsyncClient) -> None:
    res = await client.post(
        "/api/v1/auth/register", json={"email": "not-an-email", "full_name": "", "password": "123"}
    )
    assert res.status_code == 422
    error = res.json()["error"]
    assert error["code"] == "validation_error"
    locs = {tuple(d["loc"]) for d in error["details"]}
    assert ("body", "email") in locs
    assert ("body", "password") in locs


async def test_login_wrong_password_is_401(client: AsyncClient) -> None:
    await register_and_login(client, "bob@example.com")
    res = await client.post(
        "/api/v1/auth/login", data={"username": "bob@example.com", "password": "wrong-pass"}
    )
    assert res.status_code == 401
    assert res.headers["WWW-Authenticate"] == "Bearer"
    assert res.json()["error"]["code"] == "unauthorized"


async def test_me_requires_token(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/users/me")).status_code == 401
    res = await client.get("/api/v1/users/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert res.status_code == 401


async def test_refresh_rotates_and_revokes_old_token(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "carol@example.com", "full_name": "Carol", "password": "secret123"},
    )
    login = await client.post(
        "/api/v1/auth/login", data={"username": "carol@example.com", "password": "secret123"}
    )
    old_refresh = login.json()["refresh_token"]

    refreshed = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"]

    reused = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reused.status_code == 401

    new_refresh = refreshed.json()["refresh_token"]
    assert (
        await client.post("/api/v1/auth/logout", json={"refresh_token": new_refresh})
    ).status_code == 204
    after_logout = await client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert after_logout.status_code == 401


async def test_access_token_cannot_be_used_as_refresh(client: AsyncClient) -> None:
    headers = await register_and_login(client, "dave@example.com")
    access = headers["Authorization"].removeprefix("Bearer ")
    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": access})
    assert res.status_code == 401


async def test_locked_user_cannot_refresh(client: AsyncClient, engine: AsyncEngine) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "grace@example.com", "full_name": "Grace", "password": "secret123"},
    )
    login = await client.post(
        "/api/v1/auth/login", data={"username": "grace@example.com", "password": "secret123"}
    )
    tokens = login.json()
    async with engine.begin() as conn:
        await conn.execute(
            update(User).where(User.email == "grace@example.com").values(is_active=False)
        )

    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert res.status_code == 401
    assert res.json()["error"]["message"] == messages.ACCOUNT_LOCKED

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert (await client.get("/api/v1/users/me", headers=headers)).status_code == 403


async def test_change_password_revokes_refresh_tokens(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={"email": "eve@example.com", "full_name": "Eve", "password": "secret123"},
    )
    login = await client.post(
        "/api/v1/auth/login", data={"username": "eve@example.com", "password": "secret123"}
    )
    tokens = login.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    res = await client.post(
        "/api/v1/users/me/change-password",
        json={"current_password": "secret123", "new_password": "newsecret456"},
        headers=headers,
    )
    assert res.status_code == 204
    assert (
        await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    ).status_code == 401
    relogin = await client.post(
        "/api/v1/auth/login", data={"username": "eve@example.com", "password": "newsecret456"}
    )
    assert relogin.status_code == 200


async def test_update_profile(client: AsyncClient) -> None:
    headers = await register_and_login(client, "frank@example.com")
    res = await client.patch("/api/v1/users/me", json={"full_name": "Frank Vu"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["full_name"] == "Frank Vu"


async def test_password_longer_than_72_bytes_is_422_not_500(client: AsyncClient) -> None:
    res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "long@example.com",
            "full_name": "Long",
            "password": "ă" * 40,
        },  # 40 ký tự = 80 byte
    )
    assert res.status_code == 422
    assert "72 byte" in res.json()["error"]["details"][0]["msg"]
