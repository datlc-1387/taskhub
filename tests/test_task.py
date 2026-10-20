from httpx import AsyncClient

from tests.conftest import user_id_of


async def add_member(
    client: AsyncClient, owner: dict[str, str], workspace: str, headers: dict[str, str], role: str
) -> str:
    uid = await user_id_of(client, headers)
    res = await client.post(
        f"/api/v1/workspaces/{workspace}/members",
        json={"user_id": uid, "role": role},
        headers=owner,
    )
    assert res.status_code == 201, res.text
    return uid


async def test_task_crud_with_labels_and_assignee(
    client: AsyncClient, owner: dict[str, str], member: dict[str, str], workspace: str, project: str
) -> None:
    member_id = await add_member(client, owner, workspace, member, "EDITOR")
    label = await client.post(
        f"/api/v1/projects/{project}/labels",
        json={"name": "bug", "color": "#ff0000"},
        headers=owner,
    )
    assert label.status_code == 201
    label_id = label.json()["id"]

    res = await client.post(
        f"/api/v1/projects/{project}/tasks",
        json={
            "title": "Viết API login",
            "priority": "HIGH",
            "assignee_id": member_id,
            "label_ids": [label_id],
            "due_date": "2026-12-31T00:00:00Z",
        },
        headers=owner,
    )
    assert res.status_code == 201, res.text
    task = res.json()
    assert task["status"] == "TODO"
    assert task["assignee_id"] == member_id
    assert [lb["name"] for lb in task["labels"]] == ["bug"]

    res = await client.patch(
        f"/api/v1/tasks/{task['id']}", json={"status": "IN_PROGRESS"}, headers=member
    )
    assert res.status_code == 200 and res.json()["status"] == "IN_PROGRESS"

    res = await client.delete(f"/api/v1/tasks/{task['id']}/labels/{label_id}", headers=member)
    assert res.status_code == 200 and res.json()["labels"] == []

    assert (await client.delete(f"/api/v1/tasks/{task['id']}", headers=owner)).status_code == 204
    assert (await client.get(f"/api/v1/tasks/{task['id']}", headers=owner)).status_code == 404


async def test_assignee_must_be_workspace_member(
    client: AsyncClient, owner: dict[str, str], member: dict[str, str], project: str
) -> None:
    outsider_id = await user_id_of(client, member)
    res = await client.post(
        f"/api/v1/projects/{project}/tasks",
        json={"title": "X", "assignee_id": outsider_id},
        headers=owner,
    )
    assert res.status_code == 404
    assert "not a member" in res.json()["error"]["message"]


async def test_label_from_other_project_is_rejected(
    client: AsyncClient, owner: dict[str, str], workspace: str, project: str
) -> None:
    other = await client.post(
        f"/api/v1/workspaces/{workspace}/projects", json={"name": "Other"}, headers=owner
    )
    other_label = await client.post(
        f"/api/v1/projects/{other.json()['id']}/labels", json={"name": "x"}, headers=owner
    )
    res = await client.post(
        f"/api/v1/projects/{project}/tasks",
        json={"title": "T", "label_ids": [other_label.json()["id"]]},
        headers=owner,
    )
    assert res.status_code == 404


async def test_list_tasks_filter_pagination_and_cache_invalidation(
    client: AsyncClient, owner: dict[str, str], project: str
) -> None:
    for i in range(5):
        priority = "HIGH" if i % 2 == 0 else "LOW"
        res = await client.post(
            f"/api/v1/projects/{project}/tasks",
            json={"title": f"Task {i}", "priority": priority},
            headers=owner,
        )
        assert res.status_code == 201

    res = await client.get(f"/api/v1/projects/{project}/tasks?page=1&limit=2", headers=owner)
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 5 and len(body["items"]) == 2 and body["page"] == 1

    res = await client.get(f"/api/v1/projects/{project}/tasks?priority=HIGH", headers=owner)
    assert res.json()["total"] == 3
    assert all(t["priority"] == "HIGH" for t in res.json()["items"])

    # The result is currently cached;
    # creating an additional task requires invalidating the cache so that the total increases.
    await client.post(
        f"/api/v1/projects/{project}/tasks",
        json={"title": "Task 5", "priority": "HIGH"},
        headers=owner,
    )
    res = await client.get(f"/api/v1/projects/{project}/tasks?priority=HIGH", headers=owner)
    assert res.json()["total"] == 4

    assert (
        await client.get(f"/api/v1/projects/{project}/tasks?page=0", headers=owner)
    ).status_code == 422
    assert (
        await client.get(f"/api/v1/projects/{project}/tasks?status=NOPE", headers=owner)
    ).status_code == 422


async def test_viewer_can_comment_but_not_edit_task(
    client: AsyncClient, owner: dict[str, str], member: dict[str, str], workspace: str, project: str
) -> None:
    await add_member(client, owner, workspace, member, "VIEWER")
    task = (
        await client.post(f"/api/v1/projects/{project}/tasks", json={"title": "T"}, headers=owner)
    ).json()

    res = await client.patch(f"/api/v1/tasks/{task['id']}", json={"status": "DONE"}, headers=member)
    assert res.status_code == 403

    res = await client.post(
        f"/api/v1/tasks/{task['id']}/comments", json={"content": "Hi"}, headers=member
    )
    assert res.status_code == 201
    comment_id = res.json()["id"]

    other = (
        await client.post(
            f"/api/v1/tasks/{task['id']}/comments", json={"content": "Owner"}, headers=owner
        )
    ).json()
    # Viewers cannot delete others' comments,
    # but they can delete their own; the owner can delete any comment.
    assert (
        await client.delete(f"/api/v1/tasks/{task['id']}/comments/{other['id']}", headers=member)
    ).status_code == 403
    assert (
        await client.delete(f"/api/v1/tasks/{task['id']}/comments/{comment_id}", headers=member)
    ).status_code == 204
    assert (
        await client.delete(f"/api/v1/tasks/{task['id']}/comments/{other['id']}", headers=owner)
    ).status_code == 204
    assert (await client.get(f"/api/v1/tasks/{task['id']}/comments", headers=owner)).json() == []
