from httpx import AsyncClient


async def test_health_check(client: AsyncClient) -> None:
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    assert "X-Request-ID" in res.headers
    assert "X-Process-Time-Ms" in res.headers
