from __future__ import annotations

import time

import jwt
import pytest
from fastapi.testclient import TestClient


def test_require_auth_missing_token_returns_401(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    monkeypatch.setenv("SENTINEL_REQUIRE_AUTH", "true")
    monkeypatch.setenv("SENTINEL_JWT_SECRET", "unit-test-secret")
    from authdeps import clear_auth_settings_cache

    clear_auth_settings_cache()
    r = client.get("/api/version")
    assert r.status_code == 401


def test_require_auth_valid_analyst_token(
    monkeypatch: pytest.MonkeyPatch, client: TestClient
) -> None:
    monkeypatch.setenv("SENTINEL_REQUIRE_AUTH", "true")
    monkeypatch.setenv("SENTINEL_JWT_SECRET", "unit-test-secret")
    from authdeps import clear_auth_settings_cache

    clear_auth_settings_cache()
    token = jwt.encode(
        {
            "sub": "user-1",
            "role": "analyst",
            "exp": int(time.time()) + 3600,
        },
        "unit-test-secret",
        algorithm="HS256",
    )
    r = client.get("/api/version", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["service"] == "sentinel-api"


def test_correlation_id_echoed(client: TestClient) -> None:
    r = client.get("/health", headers={"X-Correlation-ID": "cid-abc"})
    assert r.status_code == 200
    assert r.headers.get("X-Correlation-ID") == "cid-abc"
