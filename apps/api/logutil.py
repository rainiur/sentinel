"""UTC structured log lines (JSON) for key API events — no secrets in kwargs."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

_logger = logging.getLogger("sentinel.api")


def emit(event: str, level: int = logging.INFO, **fields: Any) -> None:
    payload = {
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "event": event,
        **fields,
    }
    _logger.log(level, json.dumps(payload, default=str))


def configure_logging() -> None:
    if not logging.root.handlers:
        logging.basicConfig(level=logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
