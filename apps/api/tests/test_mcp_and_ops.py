from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def test_mcp_servers_unconfigured(client: TestClient) -> None:
    r = client.get("/api/mcp/servers")
    assert r.status_code == 200
    body = r.json()
    assert body["loaded"] is False
    assert body["path_configured"] is False
    assert body["server_count"] == 0
    assert body.get("suppressed_server_count", 0) == 0


def test_mcp_servers_loads_example_config(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = _repo_root() / "config" / "mcp.example.json"
    assert cfg.is_file()
    monkeypatch.setenv("SENTINEL_MCP_CONFIG", str(cfg))
    r = client.get("/api/mcp/servers")
    assert r.status_code == 200
    body = r.json()
    assert body["loaded"] is True
    assert body["path_configured"] is True
    assert body["error"] is None
    assert body["server_count"] >= 1
    names = {s["name"] for s in body["servers"]}
    assert "pentesting" in names
    for s in body["servers"]:
        assert s["transport"] in ("stdio", "http")
    assert body.get("suppressed_server_count", 0) == 0


def test_mcp_servers_suppressed_by_disabled_env(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg = _repo_root() / "config" / "mcp.example.json"
    monkeypatch.setenv("SENTINEL_MCP_CONFIG", str(cfg))
    monkeypatch.setenv("SENTINEL_MCP_DISABLED_SERVERS", "pentesting, ssh-mcp")
    r = client.get("/api/mcp/servers")
    assert r.status_code == 200
    body = r.json()
    assert body["suppressed_server_count"] == 2
    names = {s["name"] for s in body["servers"]}
    assert "pentesting" not in names
    assert "ssh-mcp" not in names
    assert "searxng" in names or "playwright" in names


def test_mcp_servers_missing_file(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SENTINEL_MCP_CONFIG", "/nonexistent/sentinel-mcp.json")
    r = client.get("/api/mcp/servers")
    assert r.status_code == 200
    assert r.json()["error"] == "file_not_found"


def test_write_kill_switch_blocks_post(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SENTINEL_API_WRITES_DISABLED", "true")
    r = client.post("/api/projects", json={"name": "blocked"})
    assert r.status_code == 503
    assert "writes" in r.json()["detail"].lower()


def test_write_kill_switch_allows_get(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SENTINEL_API_WRITES_DISABLED", "true")
    assert client.get("/api/projects").status_code == 200


def test_version_includes_writes_disabled_flag(client: TestClient) -> None:
    r = client.get("/api/version")
    assert r.status_code == 200
    assert "writes_disabled" in r.json()
    assert r.json()["writes_disabled"] is False


def test_version_includes_rate_limit_rpm(client: TestClient) -> None:
    r = client.get("/api/version")
    assert r.status_code == 200
    assert r.json().get("rate_limit_rpm") == 0


def test_rate_limit_429_after_burst(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SENTINEL_RATE_LIMIT_RPM", "2")
    assert client.get("/api/version").status_code == 200
    assert client.get("/api/version").status_code == 200
    r = client.get("/api/version")
    assert r.status_code == 429
    assert r.json()["detail"]
    assert "Retry-After" in r.headers


def test_health_not_rate_limited(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SENTINEL_RATE_LIMIT_RPM", "1")
    assert client.get("/health").status_code == 200
    assert client.get("/health").status_code == 200
