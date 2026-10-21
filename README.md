# TaskHub API

A task management REST API built around **Workspace → Project → Task**: users create workspaces, invite members with different roles, create projects, assign tasks, attach labels, comment, and receive an email when a task is assigned to them. This is the final project of a FastAPI course, built against a 14-feature specification.

## Tech stack

| Component | Technology |
|---|---|
| Framework | FastAPI, Pydantic v2, pydantic-settings |
| Database | PostgreSQL 16, SQLAlchemy 2 (async, asyncpg), Alembic |
| Authentication | JWT (PyJWT) access + refresh tokens, bcrypt |
| Cache | Redis 7 |
| Email | aiosmtplib, Mailpit (fake SMTP server for development) |
| Server | Gunicorn + Uvicorn workers |
| Testing and code quality | pytest, pytest-asyncio, httpx, ruff, mypy (strict) |
| Package management | uv |
| Deployment | Docker, Docker Compose |

## Project structure

```
app/
├── api/v1/        # routers: receive requests, validate input, call services
├── api/deps.py    # dependencies: DB session, current user, pagination, filters, cache
├── services/      # business logic and permission checks
├── repositories/  # database queries
├── models/        # SQLAlchemy models
├── schemas/       # Pydantic request/response schemas
├── core/          # config, security, cache, logging, middleware, exceptions, openapi,
│                  # constants (validation limits), messages (error messages)
└── db/            # engine, session, Base
alembic/           # migrations
tests/             # integration tests
```

The code is layered as **router → service → repository**. Each layer has one job: routers handle HTTP, services handle business rules and permissions, repositories handle SQL. Business logic does not depend on HTTP, is easy to test, and query changes do not touch the services.

## Getting started

### Setup

Requirements: Docker and Docker Compose. To run the app directly on your machine you also need Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env
```

Open `.env` and replace the `change-me` values (`SECRET_KEY` of at least 32 characters, `REDIS_PASSWORD`, `MAILPIT_UI_AUTH`); changing `POSTGRES_PASSWORD` is recommended too. Generate a random string with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Option 1: run everything with Docker

```bash
docker compose up -d --build
```

This starts 4 containers: `db` (PostgreSQL), `redis`, `mailpit` and `app`. When the `app` container starts, `docker-entrypoint.sh` runs `alembic upgrade head` and then launches Gunicorn with `WEB_CONCURRENCY` workers (default 4).

```bash
docker compose ps              # app becomes (healthy) after a few seconds
docker compose logs -f app     # migration and request logs
docker compose down            # stop, keep data
docker compose down -v         # stop and DELETE all database data
```

### Option 2: run the app locally (development, auto-reload)

```bash
docker compose up -d db redis mailpit
uv sync
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

In this mode the app reads `.env` and reaches the services via `localhost`. When running in Docker, `docker-compose.yml` overrides `DATABASE_URL`, `REDIS_HOST` and `SMTP_HOST` with the service names (`db`, `redis`, `mailpit`).

### URLs

| | URL |
|---|---|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health check | http://localhost:8000/health |
| Mailpit (sent emails) | http://localhost:8025 |

In Swagger, click **Authorize** and enter your email in the `username` field plus your password. Swagger then attaches the access token to every request.

## Tests and code checks

```bash
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy app
```

The tests are integration tests that call the real API through `httpx.AsyncClient`, using in-memory SQLite and an in-memory cache, so Postgres and Redis do **not** need to be running. Email sending is disabled with `MAIL_ENABLED=false` and the email function is checked with `monkeypatch`. There are currently 25 tests covering auth, workspaces, tasks, cache and email.

## API

Prefix: `/api/v1`. Every endpoint except `register`, `login` and `refresh` requires the header `Authorization: Bearer <access_token>`.

| Group | Endpoints |
|---|---|
| Auth | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout` |
| Users | `GET /users/me`, `PATCH /users/me`, `POST /users/me/change-password` |
| Workspaces | `POST /workspaces`, `GET /workspaces`, `GET/PATCH/DELETE /workspaces/{workspace_id}` |
| Members | `GET/POST /workspaces/{workspace_id}/members`, `PATCH/DELETE /workspaces/{workspace_id}/members/{member_id}` |
| Projects | `GET/POST /workspaces/{workspace_id}/projects`, `GET/PATCH/DELETE /projects/{project_id}`, `POST /projects/{project_id}/archive` |
| Tasks | `GET/POST /projects/{project_id}/tasks`, `GET/PATCH/DELETE /tasks/{task_id}` |
| Labels | `GET/POST /projects/{project_id}/labels`, `PATCH/DELETE /labels/{label_id}`, `POST/DELETE /tasks/{task_id}/labels/{label_id}` |
| Comments | `GET/POST /tasks/{task_id}/comments`, `DELETE /tasks/{task_id}/comments/{comment_id}` |

`GET /projects/{project_id}/tasks` supports the filters `status`, `priority`, `assignee_id` and pagination with `page` (default 1) and `limit` (default 20, max 100). The response looks like `{"items": [...], "total", "page", "limit"}`.

### Error format

Every error (including validation errors and 500s) uses the same format:

```json
{
  "error": {
    "code": "not_found",
    "message": "Project 3f2a... does not exist.",
    "details": null
  }
}
```

| HTTP | `code` | When |
|---|---|---|
| 401 | `unauthorized` | Missing, invalid or expired token; wrong email/password |
| 403 | `forbidden` | Not enough permission, or the account is locked |
| 404 | `not_found` | Does not exist, or you are not a member of the workspace |
| 409 | `conflict` | Email already registered, user already a member, label already on the task, write on an archived project |
| 422 | `validation_error` | Invalid input; `details` lists each invalid field |
| 500 | `internal_error` | Unexpected error; the traceback is logged |

## The 14 features of the specification

| # | Feature | Main files |
|---|---|---|
| 1 | Register / login / refresh / logout (revoke) | `api/v1/auth.py`, `services/auth.py`, `core/security.py` |
| 2 | View/update profile, change password | `api/v1/users.py`, `services/user.py` |
| 3 | Workspace CRUD, members, roles | `api/v1/workspaces.py`, `services/workspace.py` |
| 4 | Project CRUD, archive | `api/v1/projects.py`, `services/project.py` |
| 5 | Task CRUD, assignment, status, priority, due date | `api/v1/tasks.py`, `services/task.py` |
| 6 | Label CRUD, attach/detach labels on tasks | `api/v1/labels.py`, `services/label.py`, `services/task.py` |
| 7 | Comments | `api/v1/tasks.py`, `services/comment.py` |
| 8 | Filtering + pagination | `api/deps.py`, `schemas/common.py`, `repositories/task.py` |
| 9 | Cache + invalidation | `core/cache.py`, `services/task.py`, `services/label.py` |
| 10 | Email on task assignment (background task) | `services/notifications.py`, `services/task.py` |
| 11 | Resource-based access control (RBAC) | `services/permissions.py`, `api/deps.py` |
| 12 | Complete Swagger/ReDoc | `main.py`, `core/openapi.py`, `api/responses.py` |
| 13 | `docker compose up` | `Dockerfile`, `docker-entrypoint.sh`, `docker-compose.yml` |
| 14 | Ruff + mypy pass | `pyproject.toml` |

## Design decisions

### Data

- **UUID primary keys**: ids cannot be guessed (`/projects/1`, `/projects/2`...) and do not reveal record counts. Generated both in Python (`uuid4`) and in the DB (`gen_random_uuid()`).
- **Native PostgreSQL enums** for roles, statuses and priorities: the DB rejects invalid values, even for writes that bypass the API.
- **Delete policy**: workspace → project → task → comment use `CASCADE`; deleting a user leaves their tasks unassigned (`SET NULL`); a user who still owns a workspace, created tasks or wrote comments cannot be deleted, preventing accidental data loss.

### Access control

Workspace roles: **VIEWER < EDITOR < OWNER**; the system role **ADMIN** is treated as OWNER everywhere. All checks live in `PermissionService` (`require_workspace/project/task(resource, min_role)`, plus `require_author_or_role` for "the author, or a high enough role"); the specification's `verify_project_manager` maps to `require_project(..., EDITOR)`.

| Minimum role | Allowed to |
|---|---|
| VIEWER | View everything, write comments |
| EDITOR | Create/update/archive projects, create/update tasks, manage labels |
| OWNER | Update/delete the workspace, manage members (grant EDITOR or VIEWER only), delete projects |
| EDITOR or creator | Delete a task |
| Author or OWNER | Delete a comment |

- **Non-members get 404, not 403**: a 403 would confirm the resource exists and help probe other users' ids.
- **Locked accounts**: cannot log in or refresh (401); requests with a still-valid access token get 403.

### Authentication

- Access tokens last 30 minutes and are not stored. Refresh tokens last 7 days and their `jti` is stored in `refresh_tokens` so they **can be revoked**.
- **Rotation**: each refresh revokes the old token and issues a new pair, so a leaked token works only once. The revoke is a single `UPDATE ... WHERE revoked = false RETURNING`, so two parallel requests with the same token cannot both succeed. Logout revokes the current token; changing the password revokes all of them.
- `SECRET_KEY` has no default: the app refuses to start without it. bcrypt runs in a thread pool so hashing never blocks the event loop.

### Concurrent requests

Duplicates (email, workspace membership, label on a task) are blocked by unique constraints in the database. The service checks first to return a clear message, and also catches `IntegrityError` for two requests arriving at the same time, so the answer is always 409, never 500.

### Cache

- Only the task list is cached (the most frequent and heaviest endpoint). Key `tasks:{project_id}:{filters}:{page}:{limit}`, TTL 60 seconds.
- Any write to tasks/labels deletes all `tasks:{project_id}:*` keys, leaving other projects untouched.
- If Redis is down the cache is skipped and the DB is read directly, with a warning logged.
- **Limitation**: the cache is cleared before the transaction commits, so stale data may survive for up to 60 seconds; the full fix is to invalidate after commit.

### Email

Sent with `BackgroundTasks` after the response is returned; only when the assignee **changes**; SMTP failures are only logged and never break the request.

### Other

- **Archiving a project** makes it read-only: creating, updating or deleting its tasks, labels and comments returns 409. Reading still works, and the project itself can still be renamed or deleted. The check runs after the permission check, so non-members still get 404.
- **Error responses in Swagger/ReDoc are generated** (`core/openapi.py`): authenticated endpoint → 401/403 (403 includes locked accounts), `{id}` in path → 404, any input → 422, all with the `ErrorResponse` schema. Responses declared on an endpoint are never overwritten; 409 (duplicates, archived project) and the more specific 401 cases (login, refresh, change password) are declared per endpoint with helpers from `api/responses.py`.
- **Constants and messages**: validation limits live in `core/constants.py` and every error message returned to clients in `core/messages.py`.
- **Middleware**: every response has `X-Request-ID` (the client's value is kept only if it is a valid UUID, otherwise a new one is generated) and `X-Process-Time-Ms`, one access log line per request. CORS only allows origins in `CORS_ORIGINS`.
- **Docker**: multi-stage build (no uv or dev dependencies in the image), non-root user, HEALTHCHECK, no secrets in the image (compose injects them at runtime). Migrations run in the entrypoint because there is one instance; with several instances they should move to a `migrate` service. The base image still has a few unfixed Debian/Python vulnerabilities (0 critical); rebuild regularly with `--pull`.
- **Database connections**: every Gunicorn worker is a separate process with its own pool, so the total is `WEB_CONCURRENCY` (default 4) × (`DB_POOL_SIZE` + `DB_MAX_OVERFLOW`, default 5 + 5) = 40 connections, well below Postgres's default `max_connections=100`. Change these numbers together.

## Limitations and future work

- Invalidate the cache after commit instead of before.
- Send the refresh token in an `httpOnly` cookie to reduce XSS risk once there is a frontend.
- Rate-limit `/auth/login` against password guessing.
- Move migrations to a dedicated service when running multiple instances.
- Add CI (GitHub Actions) running ruff, mypy and pytest on every pull request.
