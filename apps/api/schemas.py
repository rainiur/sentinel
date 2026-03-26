"""Request/response models aligned with ``schemas/openapi.yaml``."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CreateProjectRequest(BaseModel):
    name: str
    owner_team: str | None = None


class CreateProjectResponse(BaseModel):
    id: str
    name: str
    owner_team: str | None = None


class ProjectsListResponse(BaseModel):
    projects: list[CreateProjectResponse]


class HypothesisListItem(BaseModel):
    id: str
    title: str
    bug_class: str
    status: str
    priority_score: float | None = None
    confidence_score: float | None = None
    created_at: datetime | None = None


class HypothesisListResponse(BaseModel):
    project_id: str
    hypotheses: list[HypothesisListItem]


class RequestItem(BaseModel):
    caido_request_id: str
    method: str
    url: str
    host: str
    path: str
    status_code: int | None = None
    req_headers_json: dict[str, Any] | None = None
    resp_headers_json: dict[str, Any] | None = None


class RequestSyncPayload(BaseModel):
    project_id: UUID
    requests: list[RequestItem]


class FindingSyncItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source: str = "caido"
    bug_class: str = "unspecified"
    severity: str | None = None
    confidence: float | None = None


class FindingSyncPayload(BaseModel):
    project_id: UUID
    findings: list[FindingSyncItem]


class HypothesisGenerationRequest(BaseModel):
    project_id: UUID
    max_results: int = Field(default=10, ge=1, le=50)


class FeedbackRequest(BaseModel):
    object_type: str
    object_id: UUID
    feedback_type: str
    user_id: str
    notes: str | None = None


class FeedbackCreatedResponse(BaseModel):
    created: bool = True
    id: str


class HypothesisGenerateAccepted(BaseModel):
    accepted: bool = True
    project_id: str
    hypothesis_ids: list[str]


class HypothesisApproveResponse(BaseModel):
    status: str = "approved"
    hypothesis_id: str


class EnqueueJobRequest(BaseModel):
    """Queue a worker job. ``project_id`` is required for ``ingest`` and ``embeddings``."""

    type: Literal["ingest", "embeddings", "ping", "noop"]
    project_id: UUID | None = None
    payload: dict[str, Any] | None = None
    correlation_id: str | None = None

    @model_validator(mode="after")
    def require_project_for_work_jobs(self) -> EnqueueJobRequest:
        if self.type in ("ingest", "embeddings") and self.project_id is None:
            raise ValueError("project_id is required for ingest and embeddings jobs")
        return self


class EnqueueJobResponse(BaseModel):
    queued: bool = True
    job_id: str
