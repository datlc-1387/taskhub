import pytest
from httpx import AsyncClient

from tests.conftest import user_id_of


async def test_assignment_email_sent_only_when_assignee_changes(
    client: AsyncClient,
    owner: dict[str, str],
    member: dict[str, str],
    workspace: str,
    project: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[str] = []

    async def fake_send(to_email: str, task_title: str, assigned_by: str) -> None:
        sent.append(to_email)

    # TaskService imported the function by name, so patch it where it is used
    monkeypatch.setattr("app.services.task.send_assignment_email", fake_send)

    member_id = await user_id_of(client, member)
    await client.post(
        f"/api/v1/workspaces/{workspace}/members",
        json={"user_id": member_id, "role": "EDITOR"},
        headers=owner,
    )
    r = await client.post(
        f"/api/v1/projects/{project}/tasks",
        json={"title": "T", "assignee_id": member_id},
        headers=owner,
    )
    task_id = r.json()["id"]
    assert sent == ["member@example.com"]

    await client.patch(f"/api/v1/tasks/{task_id}", json={"title": "T2"}, headers=owner)
    await client.patch(f"/api/v1/tasks/{task_id}", json={"status": "IN_PROGRESS"}, headers=owner)
    assert sent == ["member@example.com"]  # editing other fields must not resend
