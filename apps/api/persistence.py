"""Postgres persistence via SQLAlchemy Core (used when ``DATABASE_URL`` is set)."""

from __future__ import annotations

import json
from uuid import UUID, uuid4

from sqlalchemy import Engine, text

from schemas import (
    CreateProjectResponse,
    FeedbackRequest,
    FindingSyncItem,
    RequestItem,
)

# In-memory scope registration when DATABASE_URL is unset (mirrors Postgres scope_manifests row).
_mem_scope_project_ids: set[str] = set()


def clear_memory_stores() -> None:
    """Reset in-memory state (tests)."""
    _mem_scope_project_ids.clear()


def register_memory_scope(project_id: str) -> None:
    _mem_scope_project_ids.add(project_id)


def memory_scope_valid(project_id: str) -> bool:
    return project_id in _mem_scope_project_ids


def scope_manifest_valid(engine: Engine, project_id: UUID) -> bool:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT allowed_hosts FROM scope_manifests
                WHERE project_id = :pid
                """
            ),
            {"pid": project_id},
        ).one_or_none()
    if row is None:
        return False
    hosts = row[0]
    if hosts is None:
        return False
    if not isinstance(hosts, list):
        return False
    return len(hosts) > 0


def fetch_hypothesis_project_id(engine: Engine, hypothesis_id: UUID) -> UUID | None:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT project_id FROM hypotheses WHERE id = :id"),
            {"id": hypothesis_id},
        ).one_or_none()
    if row is None:
        return None
    return row[0]


def insert_project(
    engine: Engine,
    *,
    name: str,
    owner_team: str | None,
) -> CreateProjectResponse:
    pid = uuid4()
    sid = uuid4()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO projects (id, name, owner_team, status)
                VALUES (:id, :name, :owner_team, 'active')
                """
            ),
            {
                "id": pid,
                "name": name,
                "owner_team": owner_team,
            },
        )
        conn.execute(
            text(
                """
                INSERT INTO scope_manifests (
                    id, project_id, allowed_hosts, allowed_schemes, allowed_ports,
                    allowed_check_families, blocked_check_families, max_rps, approval_rules_json
                ) VALUES (
                    :sid, :pid, CAST(:hosts AS jsonb), '["https"]'::jsonb, '[443]'::jsonb,
                    '[]'::jsonb, '[]'::jsonb, 2, '{}'::jsonb
                )
                """
            ),
            {
                "sid": sid,
                "pid": pid,
                "hosts": json.dumps(["*"]),
            },
        )
    return CreateProjectResponse(
        id=str(pid),
        name=name,
        owner_team=owner_team,
    )


def fetch_project(engine: Engine, project_id: UUID) -> dict | None:
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id::text, name, owner_team
                FROM projects WHERE id = :id
                """
            ),
            {"id": project_id},
        ).one_or_none()
    if row is None:
        return None
    return {"id": row[0], "name": row[1], "owner_team": row[2]}


def project_exists(engine: Engine, project_id: UUID) -> bool:
    return fetch_project(engine, project_id) is not None


def fetch_surface(engine: Engine, project_id: UUID) -> dict:
    with engine.connect() as conn:
        ep_rows = (
            conn.execute(
                text(
                    """
                SELECT id::text, method, route_pattern, content_type, auth_required
                FROM endpoints WHERE project_id = :pid
                ORDER BY route_pattern
                """
                ),
                {"pid": project_id},
            )
            .mappings()
            .all()
        )
        param_rows = (
            conn.execute(
                text(
                    """
                SELECT p.id::text AS id, p.name, p.location, p.endpoint_id::text AS endpoint_id
                FROM parameters p
                JOIN endpoints e ON e.id = p.endpoint_id
                WHERE e.project_id = :pid
                """
                ),
                {"pid": project_id},
            )
            .mappings()
            .all()
        )
        auth_rows = (
            conn.execute(
                text(
                    """
                SELECT id::text, label FROM auth_contexts
                WHERE project_id = :pid
                """
                ),
                {"pid": project_id},
            )
            .mappings()
            .all()
        )
    return {
        "project_id": str(project_id),
        "endpoints": [dict(r) for r in ep_rows],
        "parameters": [dict(r) for r in param_rows],
        "auth_contexts": [dict(r) for r in auth_rows],
    }


def insert_caido_requests(
    engine: Engine,
    project_id: UUID,
    items: list[RequestItem],
) -> int:
    sql = text(
        """
        INSERT INTO caido_requests (
            id, project_id, caido_request_id, method, url, host, path, status_code,
            req_headers_json, resp_headers_json
        ) VALUES (
            :id, :project_id, :caido_request_id, :method, :url, :host, :path, :status_code,
            CAST(:req_headers AS jsonb), CAST(:resp_headers AS jsonb)
        )
        """
    )
    n = 0
    with engine.begin() as conn:
        for item in items:
            conn.execute(
                sql,
                {
                    "id": uuid4(),
                    "project_id": project_id,
                    "caido_request_id": item.caido_request_id,
                    "method": item.method,
                    "url": item.url,
                    "host": item.host,
                    "path": item.path,
                    "status_code": item.status_code,
                    "req_headers": json.dumps(item.req_headers_json or {}),
                    "resp_headers": json.dumps(item.resp_headers_json or {}),
                },
            )
            n += 1
    return n


def insert_findings(
    engine: Engine,
    project_id: UUID,
    items: list[FindingSyncItem],
) -> int:
    sql = text(
        """
        INSERT INTO findings (
            id, project_id, source, bug_class, severity, confidence, status
        ) VALUES (
            :id, :project_id, :source, :bug_class, :severity, :confidence, 'draft'
        )
        """
    )
    n = 0
    with engine.begin() as conn:
        for item in items:
            conn.execute(
                sql,
                {
                    "id": uuid4(),
                    "project_id": project_id,
                    "source": item.source,
                    "bug_class": item.bug_class,
                    "severity": item.severity,
                    "confidence": item.confidence,
                },
            )
            n += 1
    return n


def insert_hypothesis_stub(engine: Engine, project_id: UUID) -> str:
    hid = uuid4()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO hypotheses (
                    id, project_id, title, bug_class, rationale, status
                ) VALUES (
                    :id, :project_id, :title, :bug_class, :rationale, 'queued'
                )
                """
            ),
            {
                "id": hid,
                "project_id": project_id,
                "title": "Hypothesis generation requested",
                "bug_class": "pending",
                "rationale": "Stub row until the worker runs ranked generation.",
            },
        )
    return str(hid)


def approve_hypothesis(engine: Engine, hypothesis_id: UUID) -> bool:
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                UPDATE hypotheses SET status = 'approved'
                WHERE id = :id
                RETURNING id
                """
            ),
            {"id": hypothesis_id},
        )
        return result.fetchone() is not None


def insert_feedback(engine: Engine, payload: FeedbackRequest) -> str:
    fid = uuid4()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO feedback_events (
                    id, object_type, object_id, feedback_type, user_id, notes
                ) VALUES (
                    :id, :object_type, :object_id, :feedback_type, :user_id, :notes
                )
                """
            ),
            {
                "id": fid,
                "object_type": payload.object_type,
                "object_id": payload.object_id,
                "feedback_type": payload.feedback_type,
                "user_id": payload.user_id,
                "notes": payload.notes,
            },
        )
    return str(fid)
