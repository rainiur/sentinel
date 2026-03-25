from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import db
from main import _mem_hypotheses, _mem_projects, app


@pytest.fixture(autouse=True)
def isolated_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db.get_engine.cache_clear()
    _mem_projects.clear()
    _mem_hypotheses.clear()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as c:
        yield c
