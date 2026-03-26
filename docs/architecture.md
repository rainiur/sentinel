# Architecture Notes

## Current implementation snapshot (scaffold)

As of the last doc sync with the repo:

- **API** (FastAPI): Serves REST endpoints; uses **Postgres** when `DATABASE_URL` is set (Docker Compose sets this), otherwise **in-memory** stores for local/tests. SQLAlchemy provides the **engine**; persistence uses **SQLAlchemy Core** (`text()`), not ORM models yet. **`POST /api/sync/requests`** persists **`caido_requests`** and upserts **`endpoints`** (method + path, **query string stripped** for grouping). **`POST /api/sync/findings`** stores **`findings`**; **`GET /api/projects/{id}/findings`** lists them. Hypotheses **approve** / **reject** apply only while **`queued`**. Emits structured JSON log lines for selected events.
- **Worker**: Long-running process; **BRPOP** on Redis list **`sentinel:jobs`** (JSON jobs: **`noop`**, **`ping`**, stub **`ingest`**, **`embeddings`**); periodic heartbeat; **redacted** DB/Redis URLs in logs. The API **`POST /api/jobs`** **LPUSH**es to the same queue when **`REDIS_URL`** is set. Clustering / sub-agent job kinds not implemented yet.
- **Web**: Next.js App Router; **production image** uses standalone output. Browser calls API via `NEXT_PUBLIC_API_BASE_URL` (Compose defaults to host port **30880**). Minimal UI: **projects** (create + list), **surface**, **hypotheses** (generate / approve / reject), **findings** list.
- **Compose**: Internal service DNS (`postgres`, `redis`, `minio`); **published host ports** are configurable via `infra/docker/.env` to avoid clashes with local software.

Planned behavior (auth, RBAC, policy engine, full worker pipelines) matches the sections below but is **not** fully implemented yet.

## Service boundaries

### API
Handles authentication (optional JWT HS256 with `SENTINEL_REQUIRE_AUTH`), **analyst/admin** RBAC on `/api/*`, **audit** logging per request (`audit_http`, `X-Correlation-ID`), **scope manifest** checks before sync and hypothesis writes, domain models, orchestration, approvals, and reporting requests.

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
**MCP server sub-agents:** each configured **`mcpServers`** entry (in **`SENTINEL_MCP_CONFIG`**) maps to **one sub-agent** dedicated to that server’s tools. **Domain sub-agents** (surface, hypotheses, evidence, etc.) handle product logic and retrieval and **delegate** to named MCP sub-agents when a task needs a specific tool surface. All MCP use stays **allowlisted**, rate-limited, scope-checked, and audit-logged. Caido remains the primary source of proxy-native traffic and operator workflow context; MCP extends **testing and evidence** workflows where explicitly permitted.

**Intended server set:** sources may live under `…/Programs/MCP/` (**`pentesting`**, **`searxng-docker`**, **`ssh-mcp-server`**, **`playwright-mcp`** — see **`PLAN.md`**). **Runtime** is not a single host: Sentinel will read **`SENTINEL_MCP_CONFIG`**, a JSON file with **`mcpServers`** in the same shape as Cursor’s **`mcp.json`** (per-server `command`/`args`/`env` and/or `url`/`headers`). See **`config/mcp.example.json`**. Treat **SSH** and **Playwright** tool families as especially sensitive at the policy boundary.

## Key trust boundaries

1. User browser -> Web/API
2. API -> Postgres/Redis/Object storage
3. API <-> Model providers
4. API <-> Caido bridge
5. Research ingestion -> retrieval store
6. **Sub-agent runtime -> MCP servers** (treat as high privilege: validate every call against scope manifest and tool policy; never trust model-produced hostnames or secrets)

Treat external research and user-supplied documents as untrusted content.
