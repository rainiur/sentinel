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
- **planned**: orchestrated **sub-agent** steps and **MCP tool** invocations that are policy-checked, scoped, and audited before side effects

### Web
Provides analyst and admin console.

### Caido bridge
Acts as the in-tool operator interface and artifact exporter.

### Orchestration / MCP plane (planned)
Sub-agents coordinate reasoning and retrieval; **MCP servers** expose tools (browser automation, scanners, ticketing, etc.) used **only** through an allowlisted, rate-limited client with structured logging. Caido remains the primary source of proxy-native traffic and operator workflow context; MCP extends **testing and evidence** workflows where explicitly permitted.

**Intended server set (lab):** sources live under `…/Programs/MCP/` as **`pentesting`**, **`searxng-docker`**, **`ssh-mcp-server`**, and **`playwright-mcp`** (see **`PLAN.md`** → *Reference MCP inventory* for full paths). Deployed instances are expected reachable at **`192.168.8.70`**; Sentinel reads host and per-server endpoints from environment (see `infra/docker/.env.example`). Treat **SSH** and **Playwright** tool families as especially sensitive at the policy boundary.

## Key trust boundaries

1. User browser -> Web/API
2. API -> Postgres/Redis/Object storage
3. API <-> Model providers
4. API <-> Caido bridge
5. Research ingestion -> retrieval store
6. **Sub-agent runtime -> MCP servers** (treat as high privilege: validate every call against scope manifest and tool policy; never trust model-produced hostnames or secrets)

Treat external research and user-supplied documents as untrusted content.
