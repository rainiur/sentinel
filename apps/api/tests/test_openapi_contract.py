from __future__ import annotations

from pathlib import Path

import yaml
from fastapi import FastAPI
from fastapi.routing import APIRoute
from openapi_spec_validator import validate

from main import app


def _repo_root() -> Path:
    """tests/ -> apps/api -> apps -> repository root."""
    return Path(__file__).resolve().parent.parent.parent.parent


def _openapi_path() -> Path:
    return _repo_root() / "schemas" / "openapi.yaml"


def _load_spec() -> dict:
    path = _openapi_path()
    assert path.is_file(), f"Missing OpenAPI spec: {path}"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _spec_operations(spec: dict) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for path, item in spec.get("paths", {}).items():
        for method, body in item.items():
            m = method.upper()
            if m not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
                continue
            if not isinstance(body, dict):
                continue
            out.add((m, path))
    return out


def _app_operations(application: FastAPI) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for route in application.routes:
        if isinstance(route, APIRoute):
            for method in route.methods:
                if method in ("HEAD", "OPTIONS"):
                    continue
                out.add((method.upper(), route.path))
    return out


def test_openapi_yaml_validates() -> None:
    spec = _load_spec()
    validate(spec)


def test_openapi_path_method_parity_with_fastapi() -> None:
    spec = _load_spec()
    spec_ops = _spec_operations(spec)
    app_ops = _app_operations(app)
    assert spec_ops == app_ops, (
        f"OpenAPI spec and FastAPI routes differ.\n"
        f"Only in app: {sorted(app_ops - spec_ops)}\n"
        f"Only in spec: {sorted(spec_ops - app_ops)}"
    )
