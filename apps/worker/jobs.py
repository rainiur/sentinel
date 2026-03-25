"""Job handlers for Redis queue payloads (JSON objects)."""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger("sentinel.worker")


def process_job(job: dict[str, Any]) -> str:
    """
    Execute one job. Returns a short status for metrics/logging.

    Supported types:
    - noop: no side effects (health / plumbing).
    - ping: log-only check with optional correlation_id.
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

    log.warning("job_unknown_type type=%s job_id=%s", jtype, job_id)
    return "unknown_type"
