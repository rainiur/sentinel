# Threat Model Summary

For platform delivery milestones and what is still unimplemented in code (auth, policy, audit, etc.), see **`PLAN.md`** → *Implementation status and remaining gaps* and **`TASKS.md`**.

## Assets
- project scope manifests
- request/response artifacts
- findings and evidence
- model prompts and outputs
- API tokens and secrets
- research source registry
- **MCP server configurations** (URLs, credentials) and **tool allowlists** per project (lab reference host documented in `PLAN.md` / `SENTINEL_MCP_LAB_HOST`)

## Threats
- prompt injection through external content
- out-of-scope execution caused by weak policy enforcement
- lateral data exposure across projects
- unauthorized promotion of learning outputs
- tampering with evidence or audit logs
- secret leakage through logs or prompts
- **MCP abuse**: sub-agent or attacker-induced tool calls to non-allowlisted hosts, credential exfiltration via tool arguments, or destructive actions disguised as “testing”
- **SSRF / lateral movement** via MCP tools that accept URLs or network targets without strict validation against scope

## Controls
- content isolation and sanitization
- signed callbacks and service auth
- row-level security
- immutable audit records
- approval workflow for any action beyond read-only
- promotion pipeline with regression gates
- **deny-by-default MCP**: allowlisted servers and tools only; classify tools by risk; human approval for write/destructive classes; timeouts, rate limits, and kill switches per server or tool family
- **audit** every MCP invocation (who/what/when, redacted args, correlation id) and store outcomes as evidence where appropriate
