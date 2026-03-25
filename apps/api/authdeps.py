"""JWT authentication and RBAC dependencies (env-driven)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
_VALID_ROLES = frozenset({ROLE_ADMIN, ROLE_ANALYST})

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    sub: str
    roles: frozenset[str]

    def has_any(self, *roles: str) -> bool:
        need = frozenset(roles)
        if ROLE_ADMIN in self.roles:
            return True
        return bool(self.roles & need)


@lru_cache
def _require_auth() -> bool:
    return os.environ.get("SENTINEL_REQUIRE_AUTH", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


@lru_cache
def _jwt_secret() -> str | None:
    s = os.environ.get("SENTINEL_JWT_SECRET", "").strip()
    return s or None


def _decode_token(token: str) -> Principal:
    secret = _jwt_secret()
    if not secret:
        raise HTTPException(
            status_code=503,
            detail="Authentication is required but SENTINEL_JWT_SECRET is not configured",
        )
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    sub = str(payload.get("sub", "")).strip()
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing sub")

    role_raw = payload.get("role")
    if isinstance(role_raw, str) and role_raw.strip().lower() in _VALID_ROLES:
        roles = frozenset({role_raw.strip().lower()})
    else:
        roles = frozenset()

    if not roles:
        raise HTTPException(status_code=403, detail="Token missing valid role claim")

    return Principal(sub=sub, roles=roles)


def get_principal(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> Principal:
    """Resolve caller identity. If SENTINEL_REQUIRE_AUTH is unset/false, allow anonymous analyst."""
    if not _require_auth():
        if creds is None or not creds.credentials:
            p = Principal(sub="anonymous", roles=frozenset({ROLE_ANALYST, ROLE_ADMIN}))
            request.state.principal_sub = p.sub
            request.state.principal_roles = sorted(p.roles)
            return p
        p = _decode_token(creds.credentials)
        request.state.principal_sub = p.sub
        request.state.principal_roles = sorted(p.roles)
        return p

    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    p = _decode_token(creds.credentials)
    request.state.principal_sub = p.sub
    request.state.principal_roles = sorted(p.roles)
    return p


def require_analyst(
    principal: Annotated[Principal, Depends(get_principal)],
) -> Principal:
    if not principal.has_any(ROLE_ANALYST, ROLE_ADMIN):
        raise HTTPException(status_code=403, detail="Analyst or admin role required")
    return principal


def require_admin(
    principal: Annotated[Principal, Depends(get_principal)],
) -> Principal:
    if ROLE_ADMIN not in principal.roles:
        raise HTTPException(status_code=403, detail="Admin role required")
    return principal


def clear_auth_settings_cache() -> None:
    _require_auth.cache_clear()
    _jwt_secret.cache_clear()
