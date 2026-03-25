from __future__ import annotations

import logging
import os
import time
from urllib.parse import urlparse, urlunparse

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sentinel:sentinel@localhost:5432/sentinel")

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


def _redis_ping() -> bool:
    try:
        import redis  # noqa: PLC0415 — optional clarity at call site

        client = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2)
        return bool(client.ping())
    except Exception:  # noqa: BLE001
        return False


def main() -> None:
    log.info(
        "worker_starting redis_url=%s database_url=%s",
        redact_url(REDIS_URL),
        redact_url(DATABASE_URL),
    )
    while True:
        redis_ok = _redis_ping()
        log.info("worker_heartbeat redis_reachable=%s", redis_ok)
        time.sleep(30)


if __name__ == "__main__":
    main()
