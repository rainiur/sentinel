"""Optional maintenance: block mutating HTTP methods on ``/api/*``."""

from __future__ import annotations

import os
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def writes_disabled() -> bool:
    v = os.getenv("SENTINEL_API_WRITES_DISABLED", "").strip().lower()
    return v in ("1", "true", "yes", "on")


class WriteKillSwitchMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if (
            writes_disabled()
            and request.url.path.startswith("/api/")
            and request.method in ("POST", "PUT", "PATCH", "DELETE")
        ):
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "API writes are disabled (SENTINEL_API_WRITES_DISABLED)",
                },
            )
        return await call_next(request)
