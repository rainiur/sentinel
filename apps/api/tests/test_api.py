from __future__ import annotations

import uuid

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_memory_mode(client: TestClient) -> None:
    r = client.get("/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["database"] == "not_configured"


def test_version(client: TestClient) -> None:
    r = client.get("/api/version")
    assert r.status_code == 200
    assert r.json()["service"] == "sentinel-api"
    assert "version" in r.json()


def test_project_crud_and_surface(client: TestClient) -> None:
    c = client.post("/api/projects", json={"name": "p1", "owner_team": "a"})
    assert c.status_code == 201
    pid = c.json()["id"]
    g = client.get(f"/api/projects/{pid}")
    assert g.status_code == 200
    s = client.get(f"/api/projects/{pid}/surface")
    assert s.status_code == 200
    assert s.json()["endpoints"] == []


def test_list_projects_includes_created(client: TestClient) -> None:
    client.post("/api/projects", json={"name": "listed"})
    r = client.get("/api/projects")
    assert r.status_code == 200
    names = {p["name"] for p in r.json()["projects"]}
    assert "listed" in names


def test_sync_requests_populates_surface_in_memory(client: TestClient) -> None:
    pid = client.post("/api/projects", json={"name": "surf"}).json()["id"]
    sync = client.post(
        "/api/sync/requests",
        json={
            "project_id": pid,
            "requests": [
                {
                    "caido_request_id": "r1",
                    "method": "GET",
                    "url": "https://example.com/api/foo",
                    "host": "example.com",
                    "path": "/api/foo",
                },
                {
                    "caido_request_id": "r2",
                    "method": "POST",
                    "url": "https://example.com/api/foo",
                    "host": "example.com",
                    "path": "/api/foo",
                },
            ],
        },
    )
    assert sync.status_code == 202
    s = client.get(f"/api/projects/{pid}/surface")
    assert s.status_code == 200
    body = s.json()
    assert len(body["endpoints"]) == 2
    methods = {e["method"] for e in body["endpoints"]}
    assert methods == {"GET", "POST"}


def test_list_hypotheses_after_generate(client: TestClient) -> None:
    pid = client.post("/api/projects", json={"name": "hyp"}).json()["id"]
    gen = client.post(
        "/api/hypotheses/generate",
        json={"project_id": pid, "max_results": 2},
    )
    assert gen.status_code == 202
    r = client.get(f"/api/projects/{pid}/hypotheses")
    assert r.status_code == 200
    assert r.json()["project_id"] == pid
    assert len(r.json()["hypotheses"]) == 2
    assert {h["status"] for h in r.json()["hypotheses"]} == {"queued"}


def test_sync_requires_project(client: TestClient) -> None:
    fake = str(uuid.uuid4())
    r = client.post(
        "/api/sync/requests",
        json={
            "project_id": fake,
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
    assert r.status_code == 404


def test_hypothesis_flow(client: TestClient) -> None:
    pid = client.post("/api/projects", json={"name": "h"}).json()["id"]
    gen = client.post(
        "/api/hypotheses/generate",
        json={"project_id": pid, "max_results": 2},
    )
    assert gen.status_code == 202
    ids = gen.json()["hypothesis_ids"]
    assert len(ids) == 2
    ap = client.post(f"/api/hypotheses/{ids[0]}/approve")
    assert ap.status_code == 200
    assert ap.json()["status"] == "approved"
    again = client.post(f"/api/hypotheses/{ids[0]}/approve")
    assert again.status_code == 409


def test_hypothesis_reject_flow(client: TestClient) -> None:
    pid = client.post("/api/projects", json={"name": "rej"}).json()["id"]
    gen = client.post(
        "/api/hypotheses/generate",
        json={"project_id": pid, "max_results": 1},
    )
    hid = gen.json()["hypothesis_ids"][0]
    rj = client.post(f"/api/hypotheses/{hid}/reject")
    assert rj.status_code == 200
    assert rj.json()["status"] == "rejected"
    again = client.post(f"/api/hypotheses/{hid}/reject")
    assert again.status_code == 409


def test_surface_collapses_query_string_variants(client: TestClient) -> None:
    pid = client.post("/api/projects", json={"name": "q"}).json()["id"]
    sync = client.post(
        "/api/sync/requests",
        json={
            "project_id": pid,
            "requests": [
                {
                    "caido_request_id": "q1",
                    "method": "GET",
                    "url": "https://x/y?a=1",
                    "host": "x",
                    "path": "/y?a=1",
                },
                {
                    "caido_request_id": "q2",
                    "method": "GET",
                    "url": "https://x/y?b=2",
                    "host": "x",
                    "path": "/y?b=2",
                },
            ],
        },
    )
    assert sync.status_code == 202
    s = client.get(f"/api/projects/{pid}/surface").json()
    assert len(s["endpoints"]) == 1
    assert s["endpoints"][0]["route_pattern"] == "/y"


def test_evidence_register_and_list_memory(client: TestClient) -> None:
    pid = client.post("/api/projects", json={"name": "ev"}).json()["id"]
    reg = client.post(
        f"/api/projects/{pid}/evidence",
        json={"storage_key": f"projects/{pid[:8]}/bundle-1.json", "summary": "cap"},
    )
    assert reg.status_code == 201
    eid = reg.json()["id"]
    lst = client.get(f"/api/projects/{pid}/evidence")
    assert lst.status_code == 200
    bundles = lst.json()["bundles"]
    assert len(bundles) == 1
    assert bundles[0]["id"] == eid
    assert bundles[0]["storage_key"].endswith("bundle-1.json")


def test_evidence_invalid_storage_key_rejected(client: TestClient) -> None:
    pid = client.post("/api/projects", json={"name": "ev2"}).json()["id"]
    bad = client.post(
        f"/api/projects/{pid}/evidence",
        json={"storage_key": "bad\nkey"},
    )
    assert bad.status_code == 422


def test_list_findings_after_sync_memory(client: TestClient) -> None:
    pid = client.post("/api/projects", json={"name": "f"}).json()["id"]
    sf = client.post(
        "/api/sync/findings",
        json={
            "project_id": pid,
            "findings": [
                {"source": "caido", "bug_class": "xss", "severity": "medium"},
            ],
        },
    )
    assert sf.status_code == 202
    r = client.get(f"/api/projects/{pid}/findings")
    assert r.status_code == 200
    data = r.json()
    assert data["project_id"] == pid
    assert len(data["findings"]) == 1
    assert data["findings"][0]["bug_class"] == "xss"
    assert data["findings"][0]["status"] == "draft"


def test_feedback_no_echo(client: TestClient) -> None:
    oid = str(uuid.uuid4())
    r = client.post(
        "/api/feedback",
        json={
            "object_type": "hypothesis",
            "object_id": oid,
            "feedback_type": "helpful",
            "user_id": "u1",
            "notes": "secret note",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body.get("created") is True
    assert "id" in body
    assert "payload" not in body
    assert "secret" not in str(body)
