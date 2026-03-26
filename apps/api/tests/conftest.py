from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import db
import persistence
from authdeps import clear_auth_settings_cache
from main import _mem_endpoints, _mem_evidence, _mem_findings, _mem_hypotheses, _mem_projects, app


@pytest.fixture(autouse=True)
def isolated_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SENTINEL_REQUIRE_AUTH", raising=False)
    monkeypatch.delenv("SENTINEL_JWT_SECRET", raising=False)
    db.get_engine.cache_clear()
    clear_auth_settings_cache()
    persistence.clear_memory_stores()
    _mem_projects.clear()
    _mem_hypotheses.clear()
    _mem_endpoints.clear()
    _mem_findings.clear()
    _mem_evidence.clear()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
