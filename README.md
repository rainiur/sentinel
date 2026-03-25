# Sentinel for Caido - Build Package

**Last updated:** 2026-03-26

This package is a starter blueprint and implementation scaffold for a **human-governed, scope-bound web security testing assistant** centered on **Caido**.

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
- `docs/` - supporting design documents

## Documentation map

| Document | Purpose |
|----------|---------|
| `README.md` | How to run the stack, ports, optional host dev |
| `PLAN.md` | Goals, milestones, **implementation status and remaining gaps** |
| `TASKS.md` | Checklist backlog (kept in sync with the repo; last sync date in file header) |
| `docs/architecture.md` | Service boundaries and trust boundaries |
| `docs/threat_model.md` | Threat summary (expand as the system grows) |
| `schemas/openapi.yaml` | HTTP API contract (servers include Docker and local defaults) |
| `schemas/postgres_schema.sql` | Relational schema applied on first Postgres init in Compose |

## Principles

1. Human approval for any non-read-only action
2. Scope manifests enforced before every action
3. Deterministic checks separated from LLM reasoning
4. Learning occurs through reviewed feedback and offline promotion
5. External research ingestion is curated and allowlisted

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
| API            | http://localhost:**30880** — `GET /health`, `GET /ready`, `GET /api/version` | 8080 |
| Postgres       | **30432** | 5432 |
| Redis          | **30379** | 6379 |
| MinIO (S3 API) | **30900** | 9000 |
| MinIO console  | http://localhost:**30901** | 9001 |

The web image uses the production `runner` stage (`next build` + standalone server). The browser client’s API base URL defaults to `http://localhost:<SENTINEL_API_PORT>`. Set **`SENTINEL_BROWSER_API_URL`** in `infra/docker/.env` if you use another host or scheme.

## Optional: run services on the host

Use this only for quick iteration without rebuilding images. Python **3.10+** is recommended for the API (the API Docker image uses 3.12). Copy variables from each app’s `.env.example`.

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

API unit tests (host): `cd apps/api && pip install -r requirements-dev.txt && pytest`

## Security note

This package is designed for **authorized testing on owned or explicitly permitted assets**. Keep scope manifests, rate limits, approvals, audit logs, and source allowlists enabled from day one.
