from __future__ import annotations

import json
import uuid

import fakeredis
import pytest
from fastapi.testclient import TestClient

import jobqueue


def test_enqueue_ping_without_redis_503(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("REDIS_URL", raising=False)
    r = client.post("/api/jobs", json={"type": "ping"})
    assert r.status_code == 503
    assert "REDIS_URL" in r.json()["detail"]


def test_enqueue_ping_lpush_json(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(jobqueue, "get_redis_client", lambda: fake)
    r = client.post(
        "/api/jobs",
        json={"type": "ping", "correlation_id": "c-test"},
    )
    assert r.status_code == 202
    body = r.json()
    assert body["queued"] is True
    assert "job_id" in body
    popped = fake.brpop(jobqueue.QUEUE_KEY, timeout=1)
    assert popped is not None
    _key, raw = popped
    job = json.loads(raw)
    assert job["type"] == "ping"
    assert job["correlation_id"] == "c-test"
    assert job["job_id"] == body["job_id"]


def test_enqueue_ingest_missing_project_id_422(client: TestClient) -> None:
    r = client.post("/api/jobs", json={"type": "ingest"})
    assert r.status_code == 422


def test_enqueue_ingest_unknown_project_404(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(jobqueue, "get_redis_client", lambda: fake)
    pid = str(uuid.uuid4())
    r = client.post("/api/jobs", json={"type": "ingest", "project_id": pid})
    assert r.status_code == 404


def test_enqueue_ingest_ok_roundtrip(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(jobqueue, "get_redis_client", lambda: fake)
    pid = client.post("/api/projects", json={"name": "jq"}).json()["id"]
    r = client.post(
        "/api/jobs",
        json={
            "type": "ingest",
            "project_id": pid,
            "payload": {"kind": "requests"},
        },
    )
    assert r.status_code == 202
    popped = fake.brpop(jobqueue.QUEUE_KEY, timeout=1)
    assert popped is not None
    job = json.loads(popped[1])
    assert job["type"] == "ingest"
    assert job["project_id"] == pid
    assert job["payload"] == {"kind": "requests"}


def test_enqueue_embeddings_ok(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(jobqueue, "get_redis_client", lambda: fake)
    pid = client.post("/api/projects", json={"name": "emb"}).json()["id"]
    r = client.post(
        "/api/jobs",
        json={"type": "embeddings", "project_id": pid, "payload": {"target": "hypotheses"}},
    )
    assert r.status_code == 202
    job = json.loads(fake.brpop(jobqueue.QUEUE_KEY, timeout=1)[1])
    assert job["type"] == "embeddings"
    assert job["project_id"] == pid
