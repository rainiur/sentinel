# Architecture Notes

## Current implementation snapshot (scaffold)

As of the last doc sync with the repo:

- **API** (FastAPI): Serves REST endpoints; uses **Postgres** when `DATABASE_URL` is set (Docker Compose sets this), otherwise **in-memory** stores for local/tests. SQLAlchemy provides the **engine**; persistence uses **SQLAlchemy Core** (`text()`), not ORM models yet. Emits structured JSON log lines for selected events.
- **Worker**: Long-running process with periodic heartbeat; **redacted** DB/Redis URLs in logs; **ping** to Redis only—no job queue consumer yet.
- **Web**: Next.js App Router; **production image** uses standalone output. Browser calls API via `NEXT_PUBLIC_API_BASE_URL` (Compose defaults to host port **30880**).
- **Compose**: Internal service DNS (`postgres`, `redis`, `minio`); **published host ports** are configurable via `infra/docker/.env` to avoid clashes with local software.

Planned behavior (auth, RBAC, policy engine, full worker pipelines) matches the sections below but is **not** fully implemented yet.

## Service boundaries

### API
Handles authentication, domain models, orchestration requests, approvals, and reporting requests.

### Worker
Runs all asynchronous jobs:
- Caido ingestion processing
- embeddings
- hypothesis generation jobs
- clustering
- research fetch and parse
- evaluation

### Web
Provides analyst and admin console.

### Caido bridge
Acts as the in-tool operator interface and artifact exporter.

## Key trust boundaries

1. User browser -> Web/API
2. API -> Postgres/Redis/Object storage
3. API <-> Model providers
4. API <-> Caido bridge
5. Research ingestion -> retrieval store

Treat external research and user-supplied documents as untrusted content.
