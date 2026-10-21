import uuid

from httpx import AsyncClient


async def test_health_check(client: AsyncClient) -> None:
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    assert "X-Request-ID" in res.headers
    assert "X-Process-Time-Ms" in res.headers


async def test_request_id_accepts_only_uuid(client: AsyncClient) -> None:
    valid = "3f2a6c1e-8b7d-4e5f-9a0b-1c2d3e4f5a6b"
    res = await client.get("/health", headers={"X-Request-ID": valid})
    assert res.headers["X-Request-ID"] == valid

    for invalid in ["abc", "x" * 500, "<script>alert(1)</script>"]:
        res = await client.get("/health", headers={"X-Request-ID": invalid})
        returned = res.headers["X-Request-ID"]
        assert returned != invalid
        assert str(uuid.UUID(returned)) == returned
