"""Job handlers for Redis queue payloads (JSON objects)."""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("sentinel.worker")


def _project_id_from(job: dict[str, Any]) -> str | None:
    pl = job.get("payload")
    if isinstance(pl, dict) and pl.get("project_id") is not None:
        return str(pl["project_id"])
    pid = job.get("project_id")
    return str(pid) if pid is not None else None


def process_job(job: dict[str, Any]) -> str:
    """
    Execute one job. Returns a short status for metrics/logging.

    Supported types:
    - noop: no side effects (health / plumbing).
    - ping: log-only check with optional correlation_id.
    - ingest: stub pipeline hook (project_id required); future normalization of synced data.
    - embeddings: stub hook (project_id required); future embedding writes to pgvector.
    """
    jtype = job.get("type")
    job_id = job.get("job_id", "")

    if jtype == "noop":
        log.info("job_noop job_id=%s", job_id)
        return "ok"

    if jtype == "ping":
        log.info(
            "job_ping job_id=%s correlation_id=%s",
            job_id,
            job.get("correlation_id", ""),
        )
        return "ok"

    if jtype == "ingest":
        pid = _project_id_from(job)
        if not pid:
            log.warning("job_ingest_missing_project_id job_id=%s", job_id)
            return "invalid_payload"
        pl = job.get("payload") if isinstance(job.get("payload"), dict) else {}
        kind = pl.get("kind", "")
        log.info("job_ingest job_id=%s project_id=%s kind=%s", job_id, pid, kind)
        return "ok"

    if jtype == "embeddings":
        pid = _project_id_from(job)
        if not pid:
            log.warning("job_embeddings_missing_project_id job_id=%s", job_id)
            return "invalid_payload"
        pl = job.get("payload") if isinstance(job.get("payload"), dict) else {}
        log.info(
            "job_embeddings job_id=%s project_id=%s target=%s",
            job_id,
            pid,
            pl.get("target", ""),
        )
        return "ok"

    log.warning("job_unknown_type type=%s job_id=%s", jtype, job_id)
    return "unknown_type"
