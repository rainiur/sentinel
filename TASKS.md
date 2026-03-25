# TASKS.md - Implementation Backlog

Tactical items are tracked below. Narrative status and gap summary: **`PLAN.md`** → *Implementation status and remaining gaps*. Last doc sync: **2026-03-25**.

## 0. Project setup
- [x] Create monorepo structure (multi-app layout: `apps/*`, `infra/docker`, `integrations/`, `schemas/`, `docs/`) — Completed: 2026-03-26
- [x] Configure root `.gitignore` — Completed: 2026-03-26
- [x] Configure `.editorconfig`, pre-commit hooks (`.pre-commit-config.yaml`, root `requirements-dev.txt`) — Completed: 2026-03-26
- [x] Add CI for lint + test + Docker build (Ruff, ESLint, pytest, compose, images on `main`) — Completed: 2026-03-26
- [ ] Add OpenAPI vs API parity checks in CI where feasible
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
- [ ] Keep OpenAPI and routes in sync in CI (contract tests or Spectral)
- [x] Implement `POST /api/hypotheses/{hypothesis_id}/approve` per OpenAPI — Completed: 2026-03-26
- [ ] Add hypothesis reject/cancel APIs if/when spec expands
- [ ] Add JWT/OIDC middleware
- [ ] Add RBAC model
- [ ] Add SQLAlchemy ORM models and Alembic (or other) migrations (engine + raw SQL exist today)
- [ ] Add audit logging middleware
- [x] Feedback responses do not echo full request bodies — Completed: 2026-03-26

## 2. Database
- [x] Initial schema delivered in `schemas/postgres_schema.sql` (applied on Postgres container first init via compose) — Completed: 2026-03-26
- [ ] Tune/add indexes for expected query patterns beyond current schema
- [x] pgvector extension and embedding-friendly tables present in schema — Completed: 2026-03-26 (usage from app TBD)
- [ ] Add row-level security strategy
- [ ] Add retention jobs for artifacts and logs

## 2b. Worker service
- [ ] Replace heartbeat stub with Redis-backed queue consumer and job types (ingest, embeddings, clustering, etc.)
- [x] Worker uses Redis client for connectivity check; dependencies declared — Completed: 2026-03-26 (full job processing still TODO)

## 3. Caido integration
- [ ] Create plugin manifest and config (expand beyond skeleton)
- [ ] Add backend sync endpoints in plugin
- [ ] Add frontend panel for project binding
- [ ] Implement normalized request export
- [ ] Implement findings export
- [ ] Implement workflow trigger scaffolding
- [ ] Add signed callback verification between Caido and API

## 4. Surface mapping
- [ ] Build request normalization pipeline (beyond storing raw `caido_requests`)
- [ ] Extract route patterns, parameters, auth contexts (worker/analytics)
- [ ] Build endpoint summary documents for retrieval
- [x] Expose `GET /api/projects/{project_id}/surface` (DB-backed when Postgres configured; empty until endpoints populated) — Completed: 2026-03-26
- [ ] Surface inventory UI tables

## 5. Hypothesis engine
- [ ] Define strict JSON schema for proposals
- [ ] Implement retrieval-augmented prompt assembly
- [ ] Add confidence and priority scoring (beyond stub rows)
- [x] Approve API — Completed: 2026-03-26 (see §1)
- [ ] Add reject/review queue APIs and OpenAPI updates
- [ ] Add UI queue and detail drawer

## 6. Evidence pipeline
- [ ] Store request/response bundles in object storage
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
- [ ] Implement scope manifest validation
- [ ] Add decision engine for action gating
- [ ] Add rate limit enforcement
- [ ] Add restricted family policies
- [ ] Add emergency kill switch

## 10. Frontend
- [ ] Add dashboard page
- [ ] Add project detail page
- [ ] Add surface inventory page
- [ ] Add hypotheses queue page
- [ ] Add evidence and findings page
- [ ] Add learning metrics page
- [ ] Add research curator page
- [ ] Add policy/admin page
- [x] Home page + API health probe — Completed: 2026-03-26

## 11. Operations
- [x] Dockerfiles for API, worker, web — Completed: 2025-03-25 (scaffold); production web `runner` stage — Completed: 2026-03-26
- [x] Docker Compose stack — Completed: 2025-03-25; non-conflicting default host ports + `.env.example` — Completed: 2026-03-26
- [x] Compose: Postgres/Redis healthchecks and `depends_on` conditions — Completed: 2026-03-26
- [ ] Document non-production defaults in compose (passwords, unauthenticated Redis) and production secrets/network posture (expand README or runbook)
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
- [x] Document reference MCP source paths and lab host `192.168.8.70` (`PLAN.md`, `docs/architecture.md`, `.env.example`, Compose env passthrough) — Completed: 2026-03-25
- [ ] Document per-server URL/port map once each MCP service’s listen address on the lab host is fixed
- [ ] Document MCP server/tool allowlist model and config surface (per-project vs global; env/vault)
- [ ] Design tool risk classes (read / write / destructive) and map to approval + audit requirements
- [ ] Implement MCP client wrapper: timeouts, retries with backoff, correlation IDs, structured audit events (no secrets in logs)
- [ ] Validate tool arguments against scope manifest (hosts, paths, methods) before invocation
- [ ] Add emergency disable / per-server kill switch in config or API
- [ ] Integrate first pilot: read-only MCP tools from worker or API path behind feature flag
- [ ] Add sub-agent orchestration boundary (queue job type or dedicated service) separate from interactive API latency
- [ ] Extend OpenAPI / internal contracts for “tool run” or “agent step” results where needed for UI replay
