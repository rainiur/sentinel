from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from main import _mem_projects


def test_sync_blocked_without_scope_manifest(client: TestClient) -> None:
    """Orphan in-memory projects without scope registration cannot sync."""
    pid = str(uuid.uuid4())
    _mem_projects[pid] = {"id": pid, "name": "orphan", "owner_team": None}
    r = client.post(
        "/api/sync/requests",
        json={
            "project_id": pid,
            "requests": [
                {
                    "caido_request_id": "1",
                    "method": "GET",
                    "url": "https://a/b",
                    "host": "a",
                    "path": "/b",
                }
            ],
        },
    )
    assert r.status_code == 409
