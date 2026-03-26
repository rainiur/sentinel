"""Presigned S3-compatible PUT URLs for evidence objects (MinIO / AWS S3)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from uuid import UUID, uuid4

import boto3
from botocore.client import Config

_MAX_NAME_LEN = 200
_MAX_EXPIRES = 7 * 24 * 3600
_MIN_EXPIRES = 60


def _env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name, "").strip()
    return v if v else default


def s3_settings_complete() -> bool:
    return all(
        _env(k)
        for k in (
            "S3_ENDPOINT",
            "S3_BUCKET",
            "S3_ACCESS_KEY",
            "S3_SECRET_KEY",
        )
    )


def _expires_seconds() -> int:
    raw = _env("S3_PRESIGN_EXPIRES_SECONDS", "900") or "900"
    try:
        n = int(raw, 10)
    except ValueError:
        n = 900
    return max(_MIN_EXPIRES, min(n, _MAX_EXPIRES))


def _region() -> str:
    return _env("S3_REGION", "us-east-1") or "us-east-1"


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=_env("S3_ENDPOINT"),
        aws_access_key_id=_env("S3_ACCESS_KEY"),
        aws_secret_access_key=_env("S3_SECRET_KEY"),
        region_name=_region(),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )


def safe_evidence_filename(filename: str) -> str:
    base = Path(filename).name.strip()
    if not base or base in (".", ".."):
        raise ValueError("invalid filename")
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", base).strip("._")
    if not cleaned or cleaned.startswith("."):
        raise ValueError("invalid filename")
    return cleaned[:_MAX_NAME_LEN]


def build_evidence_object_key(project_id: UUID, filename: str) -> str:
    safe = safe_evidence_filename(filename)
    suffix = uuid4().hex[:12]
    return f"evidence/{project_id}/{suffix}_{safe}"


def presign_put_evidence(
    project_id: UUID,
    filename: str,
    content_type: str | None,
) -> tuple[str, str, int]:
    """Return (presigned_put_url, storage_key, expires_in_seconds)."""
    if not s3_settings_complete():
        raise RuntimeError("s3_not_configured")
    bucket = _env("S3_BUCKET")
    if not bucket:
        raise RuntimeError("s3_not_configured")
    key = build_evidence_object_key(project_id, filename)
    ct = (content_type or "").strip() or "application/octet-stream"
    expires = _expires_seconds()
    params: dict[str, str] = {"Bucket": bucket, "Key": key, "ContentType": ct}
    client = _s3_client()
    url = client.generate_presigned_url(
        "put_object",
        Params=params,
        ExpiresIn=expires,
        HttpMethod="PUT",
    )
    return url, key, expires
