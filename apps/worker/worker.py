from __future__ import annotations

import json
import logging
import os
import time
from urllib.parse import urlparse, urlunparse

import redis

from jobs import process_job

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sentinel:sentinel@localhost:5432/sentinel")
JOB_QUEUE = os.getenv("SENTINEL_JOB_QUEUE", "sentinel:jobs")
BRPOP_TIMEOUT = int(os.getenv("SENTINEL_WORKER_BRPOP_TIMEOUT", "5"))
HEARTBEAT_INTERVAL_SEC = float(os.getenv("SENTINEL_WORKER_HEARTBEAT_SEC", "30"))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sentinel.worker")


def redact_url(url: str) -> str:
    """Return a URL safe to log (password masked, never full credentials)."""
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    user = parsed.username or ""
    if host:
        auth = f"{user}:***" if user else "***"
        netloc = f"{auth}@{host}{port}"
    else:
        netloc = parsed.netloc
    return urlunparse((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def run() -> None:
    log.info(
        "worker_starting redis_url=%s database_url=%s queue=%s brpop_timeout=%s",
        redact_url(REDIS_URL),
        redact_url(DATABASE_URL),
        JOB_QUEUE,
        BRPOP_TIMEOUT,
    )
    client = redis.Redis.from_url(
        REDIS_URL,
        socket_connect_timeout=5,
        decode_responses=True,
    )
    last_hb = 0.0
    while True:
        try:
            now = time.monotonic()
            if now - last_hb >= HEARTBEAT_INTERVAL_SEC:
                ok = bool(client.ping())
                log.info(
                    "worker_heartbeat redis_reachable=%s queue=%s",
                    ok,
                    JOB_QUEUE,
                )
                last_hb = now

            item = client.brpop(JOB_QUEUE, timeout=BRPOP_TIMEOUT)
            if not item:
                continue
            _key, raw = item
            try:
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise ValueError("job root must be a JSON object")
            except (json.JSONDecodeError, ValueError) as exc:
                log.warning(
                    "job_invalid_json error=%s raw_prefix=%s",
                    type(exc).__name__,
                    (raw[:120] + "…") if len(raw) > 120 else raw,
                )
                continue
            process_job(data)
        except redis.ConnectionError as exc:
            log.error("worker_redis_connection_error error=%s", type(exc).__name__)
            time.sleep(5)
        except OSError as exc:
            log.error("worker_io_error error=%s", type(exc).__name__)
            time.sleep(5)
        except Exception:  # noqa: BLE001
            log.exception("worker_loop_error")
            time.sleep(2)


def main() -> None:
    run()


if __name__ == "__main__":
    main()
