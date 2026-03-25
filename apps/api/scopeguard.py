"""Scope manifest checks before mutating operations.

Valid when a scope_manifests row exists and allowed_hosts is a non-empty list.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import Engine

import persistence


def ensure_project_scope_allows_writes(engine: Engine | None, project_id: UUID) -> None:
    if engine is not None:
        if not persistence.scope_manifest_valid(engine, project_id):
            raise HTTPException(
                status_code=409,
                detail=(
                    "Scope manifest missing or invalid for this project; "
                    "sync and writes are blocked"
                ),
            )
        return
    if not persistence.memory_scope_valid(str(project_id)):
        raise HTTPException(
            status_code=409,
            detail=(
                "Scope manifest missing or invalid for this project; sync and writes are blocked"
            ),
        )
