from httpx import AsyncClient

from tests.conftest import user_id_of


async def test_creator_becomes_owner_member(
    client: AsyncClient, owner: dict[str, str], workspace: str
) -> None:
    res = await client.get(f"/api/v1/workspaces/{workspace}/members", headers=owner)
    assert res.status_code == 200
    assert [m["role"] for m in res.json()] == ["OWNER"]

    mine = await client.get("/api/v1/workspaces", headers=owner)
    assert [w["id"] for w in mine.json()] == [workspace]


async def test_non_member_sees_404_not_403(
    client: AsyncClient, member: dict[str, str], workspace: str
) -> None:
    # do not reveal the existence of the workspace to outsiders
    assert (await client.get(f"/api/v1/workspaces/{workspace}", headers=member)).status_code == 404


async def test_viewer_cannot_create_project_but_editor_can(
    client: AsyncClient, owner: dict[str, str], member: dict[str, str], workspace: str
) -> None:
    member_id = await user_id_of(client, member)
    res = await client.post(
        f"/api/v1/workspaces/{workspace}/members",
        json={"user_id": member_id, "role": "VIEWER"},
        headers=owner,
    )
    assert res.status_code == 201

    res = await client.post(
        f"/api/v1/workspaces/{workspace}/projects", json={"name": "P1"}, headers=member
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "forbidden"

    res = await client.patch(
        f"/api/v1/workspaces/{workspace}/members/{member_id}",
        json={"role": "EDITOR"},
        headers=owner,
    )
    assert res.status_code == 200 and res.json()["role"] == "EDITOR"

    res = await client.post(
        f"/api/v1/workspaces/{workspace}/projects", json={"name": "P1"}, headers=member
    )
    assert res.status_code == 201


async def test_only_owner_manages_members(
    client: AsyncClient, owner: dict[str, str], member: dict[str, str], workspace: str
) -> None:
    owner_id = await user_id_of(client, owner)
    member_id = await user_id_of(client, member)
    await client.post(
        f"/api/v1/workspaces/{workspace}/members",
        json={"user_id": member_id, "role": "EDITOR"},
        headers=owner,
    )
    # No additional editors allowed
    res = await client.post(
        f"/api/v1/workspaces/{workspace}/members",
        json={"user_id": owner_id, "role": "VIEWER"},
        headers=member,
    )
    assert res.status_code == 403
    # owner cannot be deleted
    res = await client.delete(f"/api/v1/workspaces/{workspace}/members/{owner_id}", headers=owner)
    assert res.status_code == 403
    # duplicate entry → 409
    res = await client.post(
        f"/api/v1/workspaces/{workspace}/members",
        json={"user_id": member_id, "role": "VIEWER"},
        headers=owner,
    )
    assert res.status_code == 409
    # remove regular member → 204 and loss of access
    res = await client.delete(f"/api/v1/workspaces/{workspace}/members/{member_id}", headers=owner)
    assert res.status_code == 204
    assert (await client.get(f"/api/v1/workspaces/{workspace}", headers=member)).status_code == 404


async def test_archive_and_delete_project(
    client: AsyncClient, owner: dict[str, str], project: str
) -> None:
    res = await client.post(f"/api/v1/projects/{project}/archive", headers=owner)
    assert res.status_code == 200 and res.json()["status"] == "ARCHIVED"
    assert (await client.delete(f"/api/v1/projects/{project}", headers=owner)).status_code == 204
    assert (await client.get(f"/api/v1/projects/{project}", headers=owner)).status_code == 404
