from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import db
import persistence
import rate_limit_middleware
from authdeps import clear_auth_settings_cache
from main import _mem_endpoints, _mem_evidence, _mem_findings, _mem_hypotheses, _mem_projects, app


@pytest.fixture(autouse=True)
def isolated_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SENTINEL_REQUIRE_AUTH", raising=False)
    monkeypatch.delenv("SENTINEL_JWT_SECRET", raising=False)
    monkeypatch.delenv("SENTINEL_API_WRITES_DISABLED", raising=False)
    monkeypatch.delenv("SENTINEL_MCP_CONFIG", raising=False)
    monkeypatch.delenv("SENTINEL_RATE_LIMIT_RPM", raising=False)
    monkeypatch.delenv("SENTINEL_TRUST_X_FORWARDED_FOR", raising=False)
    for _s3k in (
        "S3_ENDPOINT",
        "S3_BUCKET",
        "S3_ACCESS_KEY",
        "S3_SECRET_KEY",
        "S3_REGION",
        "S3_PRESIGN_EXPIRES_SECONDS",
    ):
        monkeypatch.delenv(_s3k, raising=False)
    rate_limit_middleware.reset_rate_limit_state()
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
