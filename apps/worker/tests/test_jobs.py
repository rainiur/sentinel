from __future__ import annotations

import json
import uuid

import pytest

from jobs import process_job


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"type": "noop", "job_id": "a"}, "ok"),
        ({"type": "ping", "job_id": "b", "correlation_id": "c1"}, "ok"),
        (
            {
                "type": "ingest",
                "job_id": "ing-1",
                "project_id": str(uuid.uuid4()),
                "payload": {"kind": "x"},
            },
            "ok",
        ),
        (
            {
                "type": "embeddings",
                "job_id": "emb-1",
                "payload": {"project_id": str(uuid.uuid4()), "target": "t"},
            },
            "ok",
        ),
        ({"type": "ingest", "job_id": "bad-ingest"}, "invalid_payload"),
        ({"type": "embeddings", "job_id": "bad-emb"}, "invalid_payload"),
        ({"type": "unknown", "job_id": "c"}, "unknown_type"),
    ],
)
def test_process_job_status(payload: dict, expected: str) -> None:
    assert process_job(payload) == expected


def test_queue_roundtrip_fakeredis() -> None:
    import fakeredis

    r = fakeredis.FakeRedis(decode_responses=True)
    job = {"type": "noop", "job_id": "rt-1"}
    r.lpush("sentinel:jobs", json.dumps(job))
    popped = r.brpop("sentinel:jobs", timeout=1)
    assert popped is not None
    _k, raw = popped
    assert process_job(json.loads(raw)) == "ok"
