# Caido Bridge Plugin Skeleton

This package is a starter skeleton for a Caido plugin that connects a Caido workspace to the Sentinel platform.

Implementation backlog for the bridge lives in the repo root **`TASKS.md`** (section **3. Caido integration**).

## Intended capabilities
- bind a Caido project to a Sentinel project
- export normalized requests and findings
- provide a small analyst side panel in Caido
- trigger bounded workflow actions after approval
- submit analyst feedback back to Sentinel

## Package layout
- `packages/frontend` - view components and user interactions inside Caido
- `packages/backend` - export/sync logic and bridge RPC
- `packages/shared` - shared types and schemas

## Sentinel HTTP sync (no Caido SDK required for this piece)

`packages/backend/src/sentinel-sync.ts` exports:

- **`pushRequestsToSentinel(cfg, requests)`** → **`POST /api/sync/requests`** (**`RequestSyncPayload`**)
- **`pushFindingsToSentinel(cfg, findings)`** → **`POST /api/sync/findings`** (**`FindingSyncPayload`**; maps **`SentinelFinding.title`** + **`bugClass`** into API **`bug_class`**)

Configure:

- **`apiBaseUrl`** — e.g. `http://localhost:30880` when using default Compose API port
- **`projectId`** — Sentinel project UUID (create via `POST /api/projects` or after listing projects in the web UI)
- **`bearerToken`** — optional; required if the API runs with **`SENTINEL_REQUIRE_AUTH=true`**

Map proxy traffic to **`SentinelRequest`** (see `packages/shared/src/types.ts`), then call **`pushRequestsToSentinel`**. Wire that from Caido’s backend plugin hooks when you integrate the official SDK.

## Implementation notes
Use current Caido plugin and workflow SDK references while filling in the generated TODOs in `packages/backend/src/index.ts` and `packages/frontend/src/index.ts`.
