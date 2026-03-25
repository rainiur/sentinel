"""Request/response models aligned with ``schemas/openapi.yaml``."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateProjectRequest(BaseModel):
    name: str
    owner_team: Optional[str] = None


class CreateProjectResponse(BaseModel):
    id: str
    name: str
    owner_team: Optional[str] = None


class RequestItem(BaseModel):
    caido_request_id: str
    method: str
    url: str
    host: str
    path: str
    status_code: Optional[int] = None
    req_headers_json: Optional[Dict[str, Any]] = None
    resp_headers_json: Optional[Dict[str, Any]] = None


class RequestSyncPayload(BaseModel):
    project_id: UUID
    requests: List[RequestItem]


class FindingSyncItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    source: str = "caido"
    bug_class: str = "unspecified"
    severity: Optional[str] = None
    confidence: Optional[float] = None


class FindingSyncPayload(BaseModel):
    project_id: UUID
    findings: List[FindingSyncItem]


class HypothesisGenerationRequest(BaseModel):
    project_id: UUID
    max_results: int = Field(default=10, ge=1, le=50)


class FeedbackRequest(BaseModel):
    object_type: str
    object_id: UUID
    feedback_type: str
    user_id: str
    notes: Optional[str] = None


class FeedbackCreatedResponse(BaseModel):
    created: bool = True
    id: str


class HypothesisGenerateAccepted(BaseModel):
    accepted: bool = True
    project_id: str
    hypothesis_ids: List[str]


class HypothesisApproveResponse(BaseModel):
    status: str = "approved"
    hypothesis_id: str
