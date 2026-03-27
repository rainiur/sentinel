# TASKS.md - Implementation Backlog

Tactical items are tracked below. Narrative status and gap summary: **`PLAN.md`** → *Implementation status and remaining gaps*. Last doc sync: **2026-03-26** (findings & evidence inventory: filters, export, finding detail drawer).

## 0. Project setup
- [x] Create monorepo structure (multi-app layout: `apps/*`, `infra/docker`, `integrations/`, `schemas/`, `docs/`) — Completed: 2026-03-26
- [x] Configure root `.gitignore` — Completed: 2026-03-26
- [x] Configure `.editorconfig`, pre-commit hooks (`.pre-commit-config.yaml`, root `requirements-dev.txt`) — Completed: 2026-03-26
- [x] Add CI for lint + test + Docker build (Ruff, ESLint, pytest, compose, images on `main`) — Completed: 2026-03-26
- [x] Add OpenAPI vs API parity checks in CI where feasible — Completed: 2026-03-26 (validate `schemas/openapi.yaml`; pytest parity vs FastAPI routes in `apps/api/tests/test_openapi_contract.py`)
- [x] Create `.env.example` files for each service (`apps/api`, `apps/worker`, `apps/web`, `infra/docker/.env.example`) — Completed: 2026-03-26
- [x] Commit a web package lockfile (`package-lock.json`) — Completed: 2026-03-26 (npm; document policy in README if you standardize on pnpm/yarn later)
- [ ] Adopt stricter Python dependency pinning if required (pip-tools / Poetry export) for reproducible builds and SCA
- [x] Add visible last-updated date to `README.md` — Completed: 2026-03-26
- [ ] Resolve threat-model doc location vs org standard (`docs/threat_model.md` vs root `THREATMODEL.md`)
- [ ] Migrate backlog lines to required checklist format (owner, priority, target date) when program tracking starts

## 1. Backend foundation
- [x] Implement FastAPI app bootstrap — Completed: 2026-03-26
- [x] Add health, readiness, version endpoints (`/health`, `/ready`, `/api/version`) — Completed: 2026-03-26
- [x] Postgres-backed persistence when `DATABASE_URL` is set; in-memory fallback when unset — Completed: 2026-03-26
- [x] Align request/response models with `schemas/openapi.yaml` (Pydantic; not raw `dict` on sync/feedback/hypotheses) — Completed: 2026-03-26
- [x] Keep OpenAPI and routes in sync in CI (contract tests or Spectral) — Completed: 2026-03-26 (same as §0 OpenAPI parity tests)
- [x] Implement `POST /api/hypotheses/{hypothesis_id}/approve` per OpenAPI — Completed: 2026-03-26
- [x] **`POST /api/hypotheses/{id}/reject`** (queued-only; approve/reject return **409** if not queued) — Completed: 2026-03-26
- [x] Add JWT (HS256) middleware and env toggles (`SENTINEL_REQUIRE_AUTH`, `SENTINEL_JWT_SECRET`) — Completed: 2026-03-26
- [ ] Add OIDC / JWKS verification (beyond shared-secret JWT)
- [x] Add RBAC model (`analyst` / `admin` claims; admin implies full analyst access) — Completed: 2026-03-26
- [ ] Add SQLAlchemy ORM models and Alembic (or other) migrations (engine + raw SQL exist today)
- [x] Add audit logging middleware (`audit_http` JSON + `X-Correlation-ID`) — Completed: 2026-03-26
- [x] Feedback responses do not echo full request bodies — Completed: 2026-03-26

## 2. Database
- [x] Initial schema delivered in `schemas/postgres_schema.sql` (applied on Postgres container first init via compose) — Completed: 2026-03-26
- [ ] Tune/add indexes for expected query patterns beyond current schema
- [x] pgvector extension and embedding-friendly tables present in schema — Completed: 2026-03-26 (usage from app TBD)
- [ ] Add row-level security strategy
- [ ] Add retention jobs for artifacts and logs

## 2b. Worker service
- [x] Redis-backed queue consumer: **BRPOP** on **`SENTINEL_JOB_QUEUE`** (default `sentinel:jobs`), JSON jobs with **`noop`** / **`ping`** types; periodic heartbeat — Completed: 2026-03-26
- [x] Job types **ingest** and **embeddings** (stub handlers in worker); **`POST /api/jobs`** **LPUSH**es JSON to **`SENTINEL_JOB_QUEUE`** (requires **`REDIS_URL`** on API) — Completed: 2026-03-26
- [ ] Add job types **clustering**, **sub-agent** steps; additional producers as needed
- [x] Worker uses Redis client; dependencies declared — Completed: 2026-03-26

## 3. Caido integration
- [ ] Create plugin manifest and config (expand beyond skeleton)
- [x] Backend **HTTP** helper **`pushRequestsToSentinel`** → **`POST /api/sync/requests`** (`integrations/caido-bridge/packages/backend/src/sentinel-sync.ts`) — Completed: 2026-03-26
- [ ] Wire Caido SDK: export selected requests → **`pushRequestsToSentinel`**
- [ ] Add frontend panel for project binding
- [ ] Implement normalized request export
- [x] HTTP **`pushFindingsToSentinel`** → **`POST /api/sync/findings`** (bridge; Caido SDK wiring still open) — Completed: 2026-03-26
- [ ] Implement workflow trigger scaffolding
- [ ] Add signed callback verification between Caido and API

## 4. Surface mapping
- [x] Derive **`endpoints`** rows from synced requests (method + path upsert; powers **`GET .../surface`**) — Completed: 2026-03-26
- [x] Strip **query string** from paths when upserting **endpoints** / memory surface — Completed: 2026-03-26
- [ ] Build request normalization pipeline (route patterns, params; beyond path + query strip)
- [ ] Extract route patterns, parameters, auth contexts (worker/analytics)
- [ ] Build endpoint summary documents for retrieval
- [x] Expose `GET /api/projects/{project_id}/surface` (DB-backed when Postgres configured; empty until endpoints populated) — Completed: 2026-03-26
- [x] Surface inventory UI tables (`/projects/{id}/surface`, filters, CSV/JSON export) — Completed: 2026-03-26

## 5. Hypothesis engine
- [ ] Define strict JSON schema for proposals
- [ ] Implement retrieval-augmented prompt assembly
- [ ] Add confidence and priority scoring (beyond stub rows)
- [x] Approve API — Completed: 2026-03-26 (see §1)
- [x] Reject API + OpenAPI; web **Reject** control on hypotheses — Completed: 2026-03-26
- [x] Hypothesis **detail drawer** (web); list payload includes **rationale**, **supporting_evidence**, flags — Completed: 2026-03-26
- [ ] Review queue APIs (filtering, pagination, server-side)

## 6. Evidence pipeline
- [x] Register **evidence bundle** metadata (**`POST /api/projects/{id}/evidence`**, **`GET .../evidence`**) after objects exist in S3-compatible storage; web register form — Completed: 2026-03-26
- [x] Presigned **PUT** URLs for evidence (`POST /api/projects/{id}/evidence/presign`; boto3; web **Upload & register**) — Completed: 2026-03-26
- [ ] Server-side streaming upload / store request/response bodies in object storage (beyond presigned client PUT)
- [ ] Add dedupe / clustering job
- [ ] Build evidence timeline view
- [ ] Add finding draft generation
- [ ] Add analyst validation controls

## 7. Learning loop
- [x] Capture feedback events (Postgres `feedback_events` when DB configured; memory path returns id only) — Completed: 2026-03-26
- [ ] Train lightweight ranking model
- [ ] Create offline evaluation dataset
- [ ] Implement shadow scoring mode
- [ ] Add drift and regression dashboards

## 8. Research ingestion
- [ ] Build allowlisted source registry
- [ ] Add RSS / sitemap / fetch adapters
- [ ] Implement content normalization and dedupe
- [ ] Implement pattern extraction schema
- [ ] Add safety filter and curator queue
- [ ] Add promote-to-retrieval flow

## 9. Policy controls
- [x] Implement scope manifest validation stub (non-empty `allowed_hosts`; default row on API project create) — Completed: 2026-03-26
- [ ] Add decision engine for action gating
- [x] Add rate limit enforcement (`SENTINEL_RATE_LIMIT_RPM` in-process sliding window on `/api/*`; `GET /api/version` exposes `rate_limit_rpm`) — Completed: 2026-03-26
- [ ] Add restricted family policies
- [x] Emergency **read-only API** via **`SENTINEL_API_WRITES_DISABLED`** (blocks POST/PUT/PATCH/DELETE on **`/api/*`**) — Completed: 2026-03-26

## 10. Frontend
- [x] **Dashboard** (`/dashboard`) — health, version, project count, MCP summary — Completed: 2026-03-26
- [x] **Projects** list (`/projects`) with **create form**, **project detail** (surface + links), **hypotheses**, **findings**, **evidence** (`/projects/{id}/evidence`) — Completed: 2026-03-26
- [x] Add surface inventory page (filters, export) — Completed: 2026-03-26 (see §4 surface UI)
- [x] Rich hypotheses queue (detail drawer; approve/reject in list + drawer) — Completed: 2026-03-26
- [x] **Findings** & **evidence** inventory UX (filters, sort, CSV/JSON export; findings **detail drawer**) — Completed: 2026-03-26
- [ ] Add learning metrics page
- [ ] Add research curator page
- [ ] Add policy/admin page
- [x] Home page + API health probe — Completed: 2026-03-26

## 11. Operations
- [x] Dockerfiles for API, worker, web — Completed: 2025-03-25 (scaffold); production web `runner` stage — Completed: 2026-03-26
- [x] Docker Compose stack — Completed: 2025-03-25; non-conflicting default host ports + `.env.example` — Completed: 2026-03-26
- [x] Compose: MCP JSON bind-mount (`SENTINEL_MCP_HOST_FILE` → `/etc/sentinel/mcp.json`; default `config/mcp.example.json`) — Completed: 2026-03-26
- [x] Compose: Postgres/Redis healthchecks and `depends_on` conditions — Completed: 2026-03-26
- [x] Document non-production Compose defaults (passwords, Redis, internal trust) in **README** — Completed: 2026-03-26
- [ ] Production runbook: secrets, network posture, rotation
- [ ] Example Prometheus metrics
- [ ] Log aggregation strategy (correlation IDs, dashboards); API emits structured JSON for key events only
- [ ] Backup and restore runbook

## 12. Hardening
- [ ] Threat model the platform (expand `docs/threat_model.md` as the system grows)
- [ ] Add prompt injection defenses for retrieved content
- [ ] Add secure secret loading
- [ ] Add immutable audit record export
- [ ] Add model provider failover controls
- [x] Worker: do not log raw `DATABASE_URL` / credentials (redacted URLs only) — Completed: 2026-03-26

## 13. MCP and sub-agent orchestration
- [x] Document MCP via Cursor-style `mcpServers` JSON (`SENTINEL_MCP_CONFIG`, `config/mcp.example.json`; no single lab host) — Completed: 2026-03-26
- [x] Document 1:1 mapping **each `mcpServers` key → dedicated MCP sub-agent** (domain agents delegate); see `PLAN.md` / `docs/architecture.md` — Completed: 2026-03-26
- [x] **GET /api/mcp/servers** — load **`SENTINEL_MCP_CONFIG`**, return server **names** + **transport** (stdio vs http) only; no secrets — Completed: 2026-03-26
- [ ] Document MCP server/tool **allowlist** model (per-project vs global; env/vault) beyond config introspection
- [ ] Design tool risk classes (read / write / destructive) and map to approval + audit requirements
- [ ] Implement MCP client wrapper: timeouts, retries with backoff, correlation IDs, structured audit events (no secrets in logs)
- [ ] Validate tool arguments against scope manifest (hosts, paths, methods) before invocation
- [ ] Add emergency disable / per-server kill switch in config or API
- [ ] Integrate first pilot: read-only MCP tools from worker or API path behind feature flag
- [ ] Add sub-agent orchestration boundary (queue job type or dedicated service) separate from interactive API latency
- [ ] Extend OpenAPI / internal contracts for “tool run” or “agent step” results where needed for UI replay
