# PLAN.md - Sentinel for Caido

## Objective

Build a self-hosted platform that integrates with Caido to:
- ingest scoped traffic, findings, workflows, and analyst notes
- map attack surface
- generate ranked hypotheses for authorized security testing
- collect evidence and draft reports
- improve through human feedback and offline promotion
- ingest curated public security research from allowlisted sources

The platform must remain:
- human governed
- scope bound
- deterministic where possible
- retrieval-driven and evidence-backed
- safe in how it learns and promotes changes

---

## Architecture

### Core services

1. **Web frontend**
   - Next.js + TypeScript
   - Dashboard, Projects, Surface, Hypotheses, Evidence, Learning, Research, Policies, Admin

2. **API gateway / app server**
   - FastAPI
   - Authentication, RBAC, public API, orchestration entry points

3. **Worker service**
   - background jobs for sync, embeddings, clustering, research ingestion, evaluation, report generation

4. **Postgres + pgvector**
   - relational store + retrieval embeddings

5. **Redis**
   - job queue, caching, distributed locks

6. **Object storage**
   - evidence artifacts, exported findings, screenshots, request/response bundles

7. **Policy engine**
   - internal service or OPA-backed decisions

8. **Caido bridge**
   - plugin package with frontend and backend components
   - project binding, evidence export, findings sync, workflow triggers

---

## Agent model

### Surface Mapper
Produces endpoint, parameter, auth-context, and route summaries.

### Hypothesis Ranker
Suggests bounded, reviewable checks with rationale and evidence references.

### Evidence Analyst
Clusters, deduplicates, and drafts technical narratives.

### Research Curator
Ingests allowlisted external content and extracts safe, reusable defensive patterns.

### Report Drafter
Creates technical and executive-facing findings drafts.

### Learning Governor
Promotes improvements only through reviewed feedback and offline evaluation.

---

## Guardrails

- Default mode: read-only
- Every project must have a scope manifest
- Every proposed action must be checked against policy
- Any replay or workflow execution requires human approval
- State-changing actions are forbidden by default
- External research is source-allowlisted and curated
- No direct promotion of live behavior from raw learning outputs

---

## Promotion pipeline

### Observe
New prompts, scores, extraction logic, or ranking models run in logging-only mode.

### Shadow
Candidate logic runs side-by-side with production and is compared offline.

### Promote
Candidate becomes active only after:
- review
- regression evaluation pass
- rollback plan exists

---

## Milestones

### M1 - Foundation
- Auth + projects + scope manifests
- Postgres schema
- Basic API and web shell
- Caido sync endpoints
- Audit logging

### M2 - Surface mapping
- Request/finding ingestion
- Route and parameter extraction
- Surface views in UI
- Embedding-based retrieval

### M3 - Analyst copilot
- Hypothesis generation endpoint
- Evidence clustering
- Approval queue
- Draft report generation

### M4 - Learning loop
- Feedback capture
- Ranking model
- Metrics dashboard
- Evaluation harness

### M5 - Research ingestion
- Source allowlist
- Feed fetchers
- Pattern extraction
- Curator queue

### M6 - Controlled execution
- Approved deterministic templates only
- Rate limiting
- Template execution history
- Kill switch / rollback controls

---

## Implementation status and remaining gaps

The repo is a **runnable stack** (Docker Compose, Postgres init schema, API with optional persistence, production web image, worker heartbeat). Product milestones beyond M1 are still mostly ahead. Authoritative checklists live in **`TASKS.md`** (synced with this section).

### Delivered in the current scaffold

- **Compose**: Postgres (pgvector), Redis, MinIO, API, worker, web; Postgres/Redis health-gated startup; **host ports** default away from 5432/6379/8080/3000/9000/9001 (see `infra/docker/.env.example`).
- **API**: `GET /health`, `GET /ready`, `GET /api/version`; Pydantic bodies aligned with `schemas/openapi.yaml`; **Postgres persistence when `DATABASE_URL` is set** (compose), **in-memory fallback** when unset (e.g. tests); sync and feedback routes persist to DB when configured; `POST /api/hypotheses/{id}/approve`; structured JSON log lines for key events (`apps/api/logutil.py`).
- **OpenAPI**: Documents Docker default API URL (`30880`) and local uvicorn (`8080`).
- **Web**: App Router with root layout; **production `runner` image** (`next build` + standalone); dev stage in Dockerfile; `package-lock.json` committed.
- **Worker**: Redacted URL logging; optional Redis ping on heartbeat (no job queue yet).
- **Docs / examples**: `README.md` (ports, Docker-first flow, last updated), per-app `.env.example`, `infra/docker/.env.example`.
- **Tests**: API unit tests (`apps/api/tests/`, `requirements-dev.txt`).

### Remaining gaps (prioritize via M1 → M6)

- **Security / M1**: No API authentication, RBAC, or audit middleware; no scope manifest enforcement or policy engine in code.
- **Data layer**: No Alembic (or equivalent) migrations; schema evolves via `postgres_schema.sql` + manual changes; row-level security and retention jobs not implemented.
- **Worker**: No Redis-backed job consumer or real ingestion/embeddings/clustering pipelines.
- **Caido bridge**: Plugin remains TODO stubs (no signed sync to API).
- **Frontend**: Beyond home + API health check, no dashboard, projects CRUD UI, or analyst workflows.
- **Object storage**: MinIO wired in compose; API does not yet store evidence bundles in S3-compatible storage.
- **Hypotheses**: Stub generation and approve only; no reject/cancel, ranking, or RAG-backed proposals.
- **Engineering**: No root `.gitignore` / `.editorconfig` / pre-commit; **no CI**; no OpenAPI↔code parity job; no Prometheus/runbooks; Python lockfile strategy optional.
- **Docs / process**: `docs/threat_model.md` vs org-standard `THREATMODEL.md` naming still to align; `TASKS.md` may need owner/priority/dates when formal tracking starts.

---

## Non-goals for v1

- autonomous target expansion
- unrestricted execution
- self-modifying production policy
- uncontrolled web crawling
- direct learning from unreviewed raw internet content
