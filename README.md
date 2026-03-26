# Sentinel for Caido - Build Package

**Last updated:** 2026-03-26 (hypothesis reject, **GET /api/projects/{id}/findings**, findings page, query-strip for surface)

This package is a starter blueprint and implementation scaffold for a **human-governed, scope-bound web security testing assistant** centered on **Caido**, with a planned **sub-agent** layer that can invoke **allowlisted MCP tools** for testing and evidence workflows under policy and audit (see **`PLAN.md`**).

It includes:
- `PLAN.md` - architecture and delivery plan
- `TASKS.md` - implementation backlog with milestones
- `infra/docker/docker-compose.yml` - local development stack (host ports avoid 5432, 6379, 8080, 3000, 9000 by default)
- `infra/docker/.env.example` - copy to `infra/docker/.env` to override any published port
- `schemas/postgres_schema.sql` - initial database schema
- `schemas/openapi.yaml` - API contract scaffold
- `apps/api/` - FastAPI starter
- `apps/web/` - Next.js frontend starter
- `apps/worker/` - background worker starter
- `integrations/caido-bridge/` - Caido plugin package skeleton
- `config/mcp.example.json` - example MCP server definitions (Cursor-compatible `mcpServers` shape)
- `docs/` - supporting design documents

## Documentation map

| Document | Purpose |
|----------|---------|
| `README.md` | How to run the stack, ports, optional host dev |
| `PLAN.md` | Goals, milestones, Caido + **MCP/sub-agent** plan, **implementation status and remaining gaps** |
| `TASKS.md` | Checklist backlog (kept in sync with the repo; last sync date in file header) |
| `docs/architecture.md` | Service boundaries and trust boundaries |
| `docs/threat_model.md` | Threat summary (expand as the system grows) |
| `schemas/openapi.yaml` | HTTP API contract (servers include Docker and local defaults) |
| `schemas/postgres_schema.sql` | Relational schema applied on first Postgres init in Compose |
| `.github/workflows/ci.yml` | GitHub Actions CI (Ruff, API tests, ESLint, web build, Compose, Docker build) |
| `.github/BRANCH_PROTECTION.md` | How to enable branch protection on `main` |

## Continuous integration

On **push** and **pull request** to `main`, [GitHub Actions](.github/workflows/ci.yml) runs:

1. **API** — Python 3.12: Ruff check + format check, then `pytest` in `apps/api` (includes OpenAPI file validation and path/method parity vs FastAPI)
2. **Web** — Node 22: `npm ci`, `npm run lint`, `npm run build`
3. **Docker Compose (config)** — `docker compose … config` (no daemon)
4. **Docker images (build)** — build API, worker, and web (`runner`) images without pushing

### Branch protection

After CI has passed at least once on `main`, configure rules under **Settings → Branches** on GitHub. Step-by-step: **[`.github/BRANCH_PROTECTION.md`](.github/BRANCH_PROTECTION.md)**.

## Principles

1. Human approval for any non-read-only action
2. Scope manifests enforced before every action
3. Deterministic checks separated from LLM reasoning
4. Learning occurs through reviewed feedback and offline promotion
5. External research ingestion is curated and allowlisted
6. MCP servers and tools are **deny-by-default**, scoped, and audited (see `TASKS.md` §13). **Each `mcpServers` entry is a dedicated MCP sub-agent**; domain agents delegate to them. **Runtime config** is a **Cursor-style JSON file** (`mcpServers` via **`SENTINEL_MCP_CONFIG`**; start from **`config/mcp.example.json`**, local **`config/mcp.json`** gitignored). Source repos may live under `Programs/MCP/`—see **`PLAN.md`** (*Reference MCP inventory*).

## Suggested startup order

1. Build and start the full stack with Docker Compose (canonical path).
2. Postgres schema is applied automatically on first database init via the compose-mounted `schemas/postgres_schema.sql`.
3. Open the web UI and confirm API health (see **Published ports** below; defaults avoid common local services).
4. Develop and load the Caido plugin skeleton from `integrations/caido-bridge/`.
5. Connect a Caido project and test sync of requests/findings.

## Run with Docker (recommended)

Build and run all services (Postgres, Redis, MinIO, API, worker, web):

```bash
cd infra/docker
cp .env.example .env   # optional: edit ports if anything still collides
docker compose up --build -d
```

### Published ports (host → container)

Defaults avoid binding **5432**, **6379**, **8080**, **3000**, **9000**, and **9001** on the host (common Postgres, Redis, HTTP, Next dev, and MinIO defaults). Override any value in `infra/docker/.env` (see `.env.example`).

| Service        | Default host URL / port | Container |
|----------------|-------------------------|-----------|
| Web UI         | http://localhost:**30700** | 3000 |
| API            | http://localhost:**30880** — `GET /health`, `GET /ready`, `GET /api/version`, `GET /api/projects`, `POST /api/sync/requests`, … | 8080 |
| Postgres       | **30432** | 5432 |
| Redis          | **30379** | 6379 |
| MinIO (S3 API) | **30900** | 9000 |
| MinIO console  | http://localhost:**30901** | 9001 |

The web image uses the production `runner` stage (`next build` + standalone server). The browser client’s API base URL defaults to `http://localhost:<SENTINEL_API_PORT>`. Set **`SENTINEL_BROWSER_API_URL`** in `infra/docker/.env` if you use another host or scheme.

**Web UI (minimal slice):** **`/`** health probe; **`/projects`** (create form + list); project detail (**surface** after request sync); **`/projects/{id}/hypotheses`** (generate, approve, reject); **`/projects/{id}/findings`** after **`POST /api/sync/findings`** / **`pushFindingsToSentinel`**. Surface **groups** paths that differ only by **query string**.

### Postgres: existing Compose volumes

If your database was created **before** the unique index **`uq_endpoints_project_method_route`** on **`endpoints`** (see `schemas/postgres_schema.sql`), apply it once:

```sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_endpoints_project_method_route
  ON endpoints (project_id, method, route_pattern);
```

Alternatively recreate the Postgres volume (**destructive**): `docker compose down -v` then `up` again.

## Optional: run services on the host

Use this only for quick iteration without rebuilding images. Copy variables from each app’s `.env.example`.

**Python version**

- **Supported:** **3.10+** for the API code (typing / Pydantic).
- **Recommended for your `.venv`:** **3.12** — same as **`apps/api/Dockerfile`** and **GitHub Actions**; **Ruff** in `pyproject.toml` uses **`target-version = "py312"`**, so lint rules assume 3.12.

On macOS, the default `python3` is often **3.9**; that is **too old**. Install 3.12 (e.g. [python.org](https://www.python.org/downloads/) or `brew install python@3.12`) and create the venv explicitly:

```bash
python3.12 -m venv .venv
```

**Use a virtual environment** for any local `pip install` so tools stay isolated (`.venv/` is gitignored).

```bash
# once per clone, from repo root (after .venv exists and is activated)
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt           # pre-commit
pip install -r apps/api/requirements-dev.txt   # pytest, ruff, httpx, …
pre-commit install
```

```bash
# API
cd apps/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8080

# Worker
cd apps/worker
pip install -r requirements.txt
python worker.py

# Web
cd apps/web
npm install
npm run dev
```

**API unit tests (host)** (with `.venv` activated): `cd apps/api && pytest`

**Worker unit tests (host):** `pip install -r apps/worker/requirements-dev.txt && cd apps/worker && pytest`

Use **Python 3.12** in `.venv` when possible; **3.10+** is the declared minimum.

**Enqueue a worker job:** with **`REDIS_URL`** set (Compose wires it for the API), **`POST /api/jobs`** with JSON body `{"type":"ping"}` or `{"type":"ingest","project_id":"<uuid>",...}` — the API **LPUSH**es to **`sentinel:jobs`** (override with **`SENTINEL_JOB_QUEUE`**). Types **`noop`** and **`ping`** do not require a project; **`ingest`** and **`embeddings`** require an existing project and valid scope (same rules as sync).

**Enqueue via Redis CLI (manual):** with Compose Redis on host port **30379** (default), e.g.
`redis-cli -p 30379 LPUSH sentinel:jobs '{"type":"ping","job_id":"cli-1","correlation_id":"manual"}'` — the worker container logs **`job_ping`**.

### Lint / hooks (same venv)

```bash
source .venv/bin/activate   # if not already active
pre-commit run --all-files  # optional manual run
ruff check apps/api apps/worker && ruff format apps/api apps/worker --check
```

Editor defaults live in **`.editorconfig`**. Python lint/format uses **Ruff** (`pyproject.toml`); CI runs `ruff check`, `ruff format --check`, and **`npm run lint`** in `apps/web`.

## Security note

This package is designed for **authorized testing on owned or explicitly permitted assets**. Keep scope manifests, rate limits, approvals, audit logs, and source allowlists enabled from day one.

### API authentication and scope (implemented)

- **`/health`** and **`/ready`** are unauthenticated (for probes). All **`/api/*`** routes require an **analyst** (or **admin**) principal.
- **Default (Compose / dev):** `SENTINEL_REQUIRE_AUTH` unset → requests without a JWT are treated as an **anonymous analyst** (do not use exposed to the internet).
- **Production-style:** set **`SENTINEL_REQUIRE_AUTH=true`** and **`SENTINEL_JWT_SECRET`**; clients must send **`Authorization: Bearer <token>`** with HS256 JWT claims **`sub`**, **`exp`**, and **`role`** (`analyst` or `admin`).
- **Audit:** each response gets **`X-Correlation-ID`**; structured log event **`audit_http`** includes method, path, status, duration, correlation id, and **`principal_sub`** when known.
- **Writes:** sync, hypothesis generate/approve require a **valid scope manifest** for the project (Postgres: row in `scope_manifests` with non-empty `allowed_hosts`; new projects created via the API get a dev default `["*"]`). Projects created only in the DB without a manifest will get **409** on those operations until a manifest is added.
