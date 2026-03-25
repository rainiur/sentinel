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
   - coordinates specialized agents (surface, hypotheses, evidence, research, reporting)
   - does **not** call MCP tools directly without passing through policy and (where required) human approval
   - records agent plans, tool selections, and outcomes for audit and replay analysis

10. **MCP tool plane** (planned)
   - **allowlisted** MCP servers and tools per project or environment (deny-by-default)
   - credentials and endpoints supplied via secure config (vault / env), never from model text
   - timeouts, concurrency limits, and rate limits per tool family
   - normalization of tool **inputs** (scope checks) and **outputs** (storage in evidence / retrieval with redaction)

### Reference MCP inventory (intended lab)

**Source checkouts** (build, Cursor MCP config, and upstream behavior live here; paths are the primary dev layout under Nextcloud—other machines should map the same **logical** servers via env):

| Role | Path |
|------|------|
| Pentesting-oriented MCP server(s) | `/Users/davidwalden/Nextcloud/Programs/MCP/pentesting` |
| SearXNG (Docker) MCP | `/Users/davidwalden/Nextcloud/Programs/MCP/searxng-docker` |
| SSH MCP | `/Users/davidwalden/Nextcloud/Programs/MCP/ssh-mcp-server` |
| Playwright MCP | `/Users/davidwalden/Nextcloud/Programs/MCP/playwright-mcp` |

**Runtime:** these MCP endpoints are expected on LAN host **`192.168.8.70`**. Per-server **ports and transports** (stdio vs HTTP vs SSE, etc.) are defined by each project’s deployment—Sentinel must consume them only through **documented env/config** (e.g. `SENTINEL_MCP_LAB_HOST` plus future per-server URL keys), never hard-coded in application logic. SSH and browser automation tools remain **high risk**: keep them behind policy, allowlists, and approvals as in *Guardrails*.

---

## Agent model

Sub-agents are **bounded workers** (prompt + tools + retrieval) that operate under the same guardrails as the rest of the platform. They may invoke **MCP tools** only through the governed MCP plane. Examples of roles:

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

### Tool-using test agents (MCP-backed)
Specialized agents that propose **read-only** or **pre-approved** MCP calls (e.g. fetch issue details, run a scoped scan, drive a browser session) strictly within the **scope manifest** and **tool allowlist**. State-changing or high-risk tool use requires the same approval path as any other non-read-only action.

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
- **Sub-agents** cannot expand scope or bypass Caido/API policy; Caido remains the anchor for proxy-native traffic and operator context

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
- **MCP foundation (read-only first)**: registry of allowed MCP servers/tools per project; worker or API-side **MCP client** with timeouts; audit log schema for tool calls; at least one **pilot sub-agent** that uses MCP only for low-risk reads (e.g. documentation or ticket fetch) inside scope

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
- **MCP / sub-agents**: No MCP registry, client, or audited tool-call path in code yet; orchestration remains single-process API/worker without an agent runtime. **Inventory** (pentesting, searxng-docker, ssh-mcp-server, playwright-mcp sources + lab host `192.168.8.70`) is documented above and in `.env.example` files; wiring URLs/ports into the allowlist is still TODO.
- **Engineering**: OpenAPI↔code parity job, Prometheus/runbooks, and optional Python lockfile strategy still open (CI, `.gitignore`, EditorConfig, and pre-commit are in place).
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
