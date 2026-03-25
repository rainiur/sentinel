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

## Implementation notes
Use current Caido plugin and workflow SDK references while filling in the generated TODOs.
