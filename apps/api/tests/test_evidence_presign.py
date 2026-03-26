from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _new_project(client: TestClient) -> str:
    r = client.post("/api/projects", json={"name": "ev-presign"})
    assert r.status_code == 201
    return r.json()["id"]


def test_presign_503_when_s3_not_configured(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for k in (
        "S3_ENDPOINT",
        "S3_BUCKET",
        "S3_ACCESS_KEY",
        "S3_SECRET_KEY",
    ):
        monkeypatch.delenv(k, raising=False)
    pid = _new_project(client)
    r = client.post(
        f"/api/projects/{pid}/evidence/presign",
        json={"filename": "note.txt"},
    )
    assert r.status_code == 503


@patch("s3_presign.boto3.client", autospec=True)
def test_presign_returns_url_and_storage_key(
    mock_boto_client: MagicMock,
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("S3_ENDPOINT", "http://minio:9000")
    monkeypatch.setenv("S3_BUCKET", "sentinel-artifacts")
    monkeypatch.setenv("S3_ACCESS_KEY", "minio")
    monkeypatch.setenv("S3_SECRET_KEY", "minio123")
    mock_boto_client.return_value.generate_presigned_url.return_value = (
        "http://minio:9000/sentinel-artifacts/evidence/x?X-Amz-Algorithm=AWS4"
    )
    pid = _new_project(client)
    r = client.post(
        f"/api/projects/{pid}/evidence/presign",
        json={"filename": "capture.png", "content_type": "image/png"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["http_method"] == "PUT"
    assert body["content_type"] == "image/png"
    assert body["expires_in"] >= 60
    assert body["upload_url"].startswith("http://")
    assert body["storage_key"].startswith(f"evidence/{pid}/")
    assert "capture.png" in body["storage_key"] or body["storage_key"].endswith("_capture.png")
    mock_boto_client.return_value.generate_presigned_url.assert_called_once()
    call_kw = mock_boto_client.return_value.generate_presigned_url.call_args.kwargs
    assert call_kw["HttpMethod"] == "PUT"
    params = call_kw["Params"]
    assert params["Bucket"] == "sentinel-artifacts"
    assert params["ContentType"] == "image/png"
    assert params["Key"].startswith(f"evidence/{pid}/")


def test_presign_404_unknown_project(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("S3_ENDPOINT", "http://minio:9000")
    monkeypatch.setenv("S3_BUCKET", "b")
    monkeypatch.setenv("S3_ACCESS_KEY", "k")
    monkeypatch.setenv("S3_SECRET_KEY", "s")
    fake = "00000000-0000-4000-8000-000000000001"
    r = client.post(
        f"/api/projects/{fake}/evidence/presign",
        json={"filename": "x.txt"},
    )
    assert r.status_code == 404


def test_presign_rejects_bad_filename(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("S3_ENDPOINT", "http://minio:9000")
    monkeypatch.setenv("S3_BUCKET", "b")
    monkeypatch.setenv("S3_ACCESS_KEY", "k")
    monkeypatch.setenv("S3_SECRET_KEY", "s")
    pid = _new_project(client)
    r = client.post(
        f"/api/projects/{pid}/evidence/presign",
        json={"filename": "."},
    )
    assert r.status_code == 422
