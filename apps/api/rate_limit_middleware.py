"""Optional per-IP sliding-window rate limit for ``/api/*`` (in-process; single-replica)."""

from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

import logutil

_state: dict[str, deque[float]] = defaultdict(deque)
_lock = threading.Lock()
_WINDOW_SEC = 60.0


def reset_rate_limit_state() -> None:
    """Clear counters (for tests)."""
    with _lock:
        _state.clear()


def _rpm() -> int:
    raw = os.getenv("SENTINEL_RATE_LIMIT_RPM", "").strip()
    if not raw:
        return 0
    try:
        n = int(raw, 10)
    except ValueError:
        return 0
    return max(0, n)


def rate_limit_rpm_configured() -> int:
    return _rpm()


def _client_key(request: Request) -> str:
    if os.getenv("SENTINEL_TRUST_X_FORWARDED_FOR", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    ):
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip() or "unknown"
    if request.client:
        return request.client.host
    return "unknown"


def _allow(key: str, limit: int) -> tuple[bool, int]:
    now = time.monotonic()
    cutoff = now - _WINDOW_SEC
    with _lock:
        q = _state[key]
        while q and q[0] < cutoff:
            q.popleft()
        if len(q) >= limit:
            retry_after = int(max(1.0, _WINDOW_SEC - (now - q[0])))
            return False, retry_after
        q.append(now)
    return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        limit = _rpm()
        if limit <= 0 or not request.url.path.startswith("/api/"):
            return await call_next(request)
        key = _client_key(request)
        ok, retry_after = _allow(key, limit)
        if not ok:
            logutil.emit(
                "rate_limit_exceeded",
                client_key=key,
                path=request.url.path,
                method=request.method,
            )
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)
