# PLAN.md - Sentinel for Caido

## Objective

Build a self-hosted platform that integrates with **Caido** as the primary in-proxy capture and operator surface, and with **orchestrated sub-agents** that may invoke **[Model Context Protocol (MCP)](https://modelcontextprotocol.io/)** tools to support **authorized security testing** (e.g. reconnaissance helpers, scanners, browser automation, ticketed evidence fetch—**only** where policy and scope allow).

The platform must:
- ingest scoped traffic, findings, workflows, and analyst notes (from Caido and other approved connectors)
- map attack surface
- generate ranked hypotheses for authorized security testing
- collect evidence and draft reports
- improve through human feedback and offline promotion
- ingest curated public security research from allowlisted sources
- **route sub-agent work through a governed MCP plane**: allowlisted servers and tools, explicit approvals for anything beyond read-only or out-of-scope risk, and full audit of tool calls and results

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

9. **Orchestration / sub-agent runtime** (planned)
   - coordinates **two kinds** of sub-agents: **MCP server sub-agents** (one per configured `mcpServers` entry—see below) and **domain sub-agents** (surface, hypotheses, evidence, research, reporting—mostly retrieval + reasoning, may *invoke* MCP sub-agents when needed)
   - MCP traffic never bypasses policy, scope, or (where required) human approval
   - records per-agent plans, tool selections, and outcomes for audit and replay analysis

10. **MCP tool plane** (planned)
   - each entry in **`mcpServers`** (`SENTINEL_MCP_CONFIG`) corresponds to **one sub-agent** bound to that server’s tool surface (its own allowlist slice, limits, and audit stream)
   - **allowlisted** tools per server per project or environment (deny-by-default)
   - credentials and endpoints supplied via secure config (vault / env), never from model text
   - timeouts, concurrency limits, and rate limits per **server** / tool family
   - normalization of tool **inputs** (scope checks) and **outputs** (storage in evidence / retrieval with redaction)

### Reference MCP inventory and runtime config

**Source checkouts** (build and Cursor/editor MCP config live here; optional reference layout):

| Role | Example path |
|------|----------------|
| Pentesting-oriented MCP server(s) | `/Users/davidwalden/Nextcloud/Programs/MCP/pentesting` |
| SearXNG (Docker) MCP | `/Users/davidwalden/Nextcloud/Programs/MCP/searxng-docker` |
| SSH MCP | `/Users/davidwalden/Nextcloud/Programs/MCP/ssh-mcp-server` |
| Playwright MCP | `/Users/davidwalden/Nextcloud/Programs/MCP/playwright-mcp` |

**Runtime (no single “MCP host”):** Sentinel reads a **JSON config file** pointed to by **`SENTINEL_MCP_CONFIG`**, using the same top-level shape as **Cursor’s `mcp.json`**: an **`mcpServers`** object whose keys are **server names** (and **sub-agent names**—one sub-agent per key) and whose values describe each server (**`command` / `args` / `env`** for stdio, and/or **`url` / `headers`** for remote HTTP/SSE—exact transport per upstream). Copy **`config/mcp.example.json`** to **`config/mcp.json`** (gitignored), or reuse/merge entries from your Cursor config; keep **secrets** in env or headers supplied by the environment, not committed. The API/worker load this path when the MCP client is implemented. SSH and Playwright tool families remain **high risk**: policy, allowlists, and approvals as in *Guardrails*.

---

## Agent model

Sub-agents are **bounded workers** (prompt + optional tools + retrieval) under the same guardrails as the rest of the platform.

### MCP server sub-agents (1:1 with config)

Each key under **`mcpServers`** in **`SENTINEL_MCP_CONFIG`** is treated as **one sub-agent**: that agent’s only MCP tools come from **that** server (e.g. `pentesting`, `searxng`, `playwright`). The orchestrator or a domain agent may **delegate** a task to a named MCP sub-agent; policy and allowlists are evaluated **per server/sub-agent**. High-risk servers (SSH, browser automation) get stricter gates. Domain agents do **not** open ad hoc connections to arbitrary MCP endpoints—they route through these named MCP sub-agents.

### Domain sub-agents (product logic; may call MCP sub-agents)

These focus on Sentinel/Caido semantics and retrieval; they **invoke** MCP server sub-agents when a task needs that server’s tools.

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

### Delegation pattern
A domain agent (or the orchestrator) proposes **read-only** or **pre-approved** work **to a specific MCP sub-agent** (by `mcpServers` name), strictly within the **scope manifest** and **tool allowlist** for that server. State-changing or high-risk tool use uses the same approval path as any other non-read-only action.

---

## Guardrails

- Default mode: read-only
- Every project must have a scope manifest
- Every proposed action must be checked against policy
- Any replay or workflow execution requires human approval
- State-changing actions are forbidden by default
- External research is source-allowlisted and curated
- No direct promotion of live behavior from raw learning outputs
- **MCP**: only **allowlisted** servers/tools; no dynamic subscription to arbitrary MCP endpoints from model output; **secrets** for MCP auth live outside prompts; **log and retain** tool name, arguments (redacted), correlation id, and outcome for audit
- **Sub-agents** (domain and MCP server–scoped) cannot expand scope or bypass Caido/API policy; Caido remains the anchor for proxy-native traffic and operator context

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
- **MCP foundation (read-only first)**: load **`mcpServers`** from **`SENTINEL_MCP_CONFIG`**; registry of allowed servers/tools per project; worker or API-side **MCP client** with timeouts; audit log schema for tool calls; pilot **one MCP server sub-agent** (one configured server) for low-risk reads only (e.g. search or doc fetch) inside scope

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
- **MCP execution gating**: classify tools (read / write / destructive); require human approval for write+ paths; emergency disable per server or per tool family

---

## Implementation status and remaining gaps

The repo is a **runnable stack** (Docker Compose, Postgres init schema, API with optional persistence, production web image, worker heartbeat). Product milestones beyond M1 are still mostly ahead. Authoritative checklists live in **`TASKS.md`** (synced with this section).

### Delivered in the current scaffold

- **Compose**: Postgres (pgvector), Redis, MinIO, API, worker, web; Postgres/Redis health-gated startup; **host ports** default away from 5432/6379/8080/3000/9000/9001 (see `infra/docker/.env.example`).
- **API**: `GET /health`, `GET /ready`, `GET /api/version`; Pydantic bodies aligned with `schemas/openapi.yaml`; **Postgres persistence when `DATABASE_URL` is set** (compose), **in-memory fallback** when unset (e.g. tests); sync and feedback routes persist to DB when configured; `POST /api/hypotheses/{id}/approve`; structured JSON log lines for key events (`apps/api/logutil.py`).
- **OpenAPI**: Documents Docker default API URL (`30880`) and local uvicorn (`8080`).
- **Web**: App Router with root layout; **production `runner` image** (`next build` + standalone); dev stage in Dockerfile; `package-lock.json` committed.
- **Worker**: Redis **BRPOP** consumer on **`sentinel:jobs`**; job types **`noop`**, **`ping`**, stub **`ingest`** / **`embeddings`**; redacted URL logging; optional Redis ping on heartbeat.
- **Docs / examples**: `README.md` (ports, Docker-first flow, last updated), per-app `.env.example`, `infra/docker/.env.example`.
- **Tests**: API unit tests (`apps/api/tests/`, `requirements-dev.txt`).

### Remaining gaps (prioritize via M1 → M6)

- **Security / M1**: **JWT (HS256) + analyst RBAC** on `/api/*`, **audit** middleware (`audit_http`, correlation id), and **scope manifest** checks on mutating routes are implemented; **OIDC/JWKS**, persisted audit store, and **policy engine** are still open.
- **Data layer**: No Alembic (or equivalent) migrations; schema evolves via `postgres_schema.sql` + manual changes; row-level security and retention jobs not implemented.
- **Worker**: **Redis BRPOP** on **`sentinel:jobs`**; **`ingest`** / **`embeddings`** stubs; API **`POST /api/jobs`** **LPUSH** producer when **`REDIS_URL`** is set. **Clustering** / **sub-agent** job types and richer pipelines still open.
- **Caido bridge**: Repo includes **`pushRequestsToSentinel`** and **`pushFindingsToSentinel`** (HTTP to **`/api/sync/*`**); Caido SDK wiring and signed callbacks remain TODO.
- **Frontend**: **Projects** list, project **surface** (endpoints after sync), and **hypotheses** queue pages exist; no full dashboard, project CRUD forms, or richer analyst workflows yet.
- **Object storage**: MinIO wired in compose; API does not yet store evidence bundles in S3-compatible storage.
- **Hypotheses**: Stub generation; **approve** and **reject** (queued-only); no ranking or RAG-backed proposals yet.
- **MCP / sub-agents**: No MCP registry, client, or audited tool-call path in code yet; orchestration remains single-process API/worker without an agent runtime. **Config contract** is **`SENTINEL_MCP_CONFIG`** → JSON with **`mcpServers`** (Cursor-style); see **`config/mcp.example.json`**. Wiring the client and allowlist is still TODO.
- **Engineering**: Prometheus/runbooks and optional Python lockfile strategy still open; **OpenAPI↔route parity** covered by API pytest (`test_openapi_contract.py`). CI, `.gitignore`, EditorConfig, and pre-commit are in place.
- **Docs / process**: `docs/threat_model.md` vs org-standard `THREATMODEL.md` naming still to align; `TASKS.md` may need owner/priority/dates when formal tracking starts.

---

## Non-goals for v1

- autonomous target expansion
- unrestricted execution
- self-modifying production policy
- uncontrolled web crawling
- direct learning from unreviewed raw internet content
- **unbounded MCP**: arbitrary server discovery, model-chosen credentials, or tool use without scope + policy + audit
- **fully autonomous pentest agents** with no human checkpoint on impactful actions
