"""HTTP audit logging (structured JSON) and correlation IDs."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

import logutil


class AuditMiddleware(BaseHTTPMiddleware):
    """Emit audit_http after each request; propagate X-Correlation-ID."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = cid
        t0 = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        principal_sub = getattr(request.state, "principal_sub", None)
        logutil.emit(
            "audit_http",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            correlation_id=cid,
            principal_sub=principal_sub,
        )
        response.headers["X-Correlation-ID"] = cid
        return response
