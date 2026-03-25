"""Database engine (optional): set ``DATABASE_URL`` for Postgres persistence."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional, Tuple

from sqlalchemy import Engine, create_engine, text


@lru_cache(maxsize=1)
def get_engine() -> Optional[Engine]:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return None
    return create_engine(url, pool_pre_ping=True)


def check_database(engine: Engine) -> Tuple[bool, Optional[str]]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 — readiness must not leak stack traces
        return False, type(exc).__name__
    return True, None
