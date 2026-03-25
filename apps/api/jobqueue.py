"""LPUSH JSON jobs to the worker Redis queue (same contract as ``apps/worker``)."""

from __future__ import annotations

import json
import os
from typing import Any

import redis

QUEUE_KEY = os.getenv("SENTINEL_JOB_QUEUE", "sentinel:jobs")


class RedisNotConfiguredError(Exception):
    """REDIS_URL is unset or empty."""


def get_redis_client() -> redis.Redis | None:
    url = os.getenv("REDIS_URL", "").strip()
    if not url:
        return None
    return redis.Redis.from_url(
        url,
        decode_responses=True,
        socket_connect_timeout=2,
    )


def enqueue_job(job: dict[str, Any]) -> None:
    """Serialize ``job`` as JSON and LPUSH to the worker queue."""
    client = get_redis_client()
    if client is None:
        raise RedisNotConfiguredError
    client.lpush(QUEUE_KEY, json.dumps(job, default=str))
