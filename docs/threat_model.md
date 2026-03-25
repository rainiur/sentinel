# Threat Model Summary

For platform delivery milestones and what is still unimplemented in code (auth, policy, audit, etc.), see **`PLAN.md`** → *Implementation status and remaining gaps* and **`TASKS.md`**.

## Assets
- project scope manifests
- request/response artifacts
- findings and evidence
- model prompts and outputs
- API tokens and secrets
- research source registry

## Threats
- prompt injection through external content
- out-of-scope execution caused by weak policy enforcement
- lateral data exposure across projects
- unauthorized promotion of learning outputs
- tampering with evidence or audit logs
- secret leakage through logs or prompts

## Controls
- content isolation and sanitization
- signed callbacks and service auth
- row-level security
- immutable audit records
- approval workflow for any action beyond read-only
- promotion pipeline with regression gates
