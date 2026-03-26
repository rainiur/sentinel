from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from redis.exceptions import RedisError

import db
import jobqueue
import logutil
import mcpconfig
import persistence
from audit_middleware import AuditMiddleware
from authdeps import require_analyst
from rate_limit_middleware import RateLimitMiddleware, rate_limit_rpm_configured
from schemas import (
    CreateProjectRequest,
    CreateProjectResponse,
    EnqueueJobRequest,
    EnqueueJobResponse,
    EvidenceBundleItem,
    EvidenceCreatedResponse,
    EvidenceListResponse,
    FeedbackCreatedResponse,
    FeedbackRequest,
    FindingListItem,
    FindingsListResponse,
    FindingSyncItem,
    FindingSyncPayload,
    HypothesisApproveResponse,
    HypothesisGenerateAccepted,
    HypothesisGenerationRequest,
    HypothesisListItem,
    HypothesisListResponse,
    HypothesisRejectResponse,
    McpServerEntry,
    McpStatusResponse,
    ProjectsListResponse,
    RegisterEvidenceRequest,
    RequestItem,
    RequestSyncPayload,
)
from scopeguard import ensure_project_scope_allows_writes
from write_kill_switch import WriteKillSwitchMiddleware, writes_disabled

load_dotenv()

APP_VERSION = "0.1.0"

_mem_projects: dict[str, dict] = {}
_mem_hypotheses: dict[str, dict] = {}
# project_id -> internal key -> endpoint row (mirrors ``endpoints`` slice of surface in memory mode)
_mem_endpoints: dict[str, dict[str, dict]] = {}
_mem_findings: dict[str, list[dict]] = {}
_mem_evidence: dict[str, list[dict]] = {}


def _memory_merge_request_items(project_key: str, items: list[RequestItem]) -> None:
    bucket = _mem_endpoints.setdefault(project_key, {})
    for item in items:
        route = persistence.normalize_route_pattern(item.path)
        method = (item.method or "GET").strip().upper() or "GET"
        ik = f"{method}\x00{route}"
        if ik not in bucket:
            bucket[ik] = {
                "id": str(uuid4()),
                "method": method,
                "route_pattern": route,
                "content_type": None,
                "auth_required": None,
            }


def _memory_append_findings(project_key: str, items: list[FindingSyncItem]) -> None:
    bucket = _mem_findings.setdefault(project_key, [])
    for it in items:
        fid = str(uuid4())
        now = datetime.now(UTC)
        bucket.insert(
            0,
            {
                "id": fid,
                "source": it.source,
                "bug_class": it.bug_class,
                "severity": it.severity,
                "confidence": it.confidence,
                "status": "draft",
                "created_at": now,
            },
        )


def _memory_append_evidence(project_key: str, storage_key: str, summary: str | None) -> str:
    eid = str(uuid4())
    now = datetime.now(UTC)
    bucket = _mem_evidence.setdefault(project_key, [])
    bucket.insert(
        0,
        {
            "id": eid,
            "storage_key": storage_key,
            "summary": summary,
            "created_at": now,
        },
    )
    return eid


@asynccontextmanager
async def lifespan(app: FastAPI):
    logutil.configure_logging()
    engine = db.get_engine()
    logutil.emit(
        "api_startup",
        version=APP_VERSION,
        persistence="postgres" if engine else "memory",
    )
    yield


app = FastAPI(
    title="Sentinel for Caido API",
    version=APP_VERSION,
    lifespan=lifespan,
)
app.add_middleware(AuditMiddleware)
app.add_middleware(WriteKillSwitchMiddleware)
app.add_middleware(RateLimitMiddleware)

api_router = APIRouter(prefix="/api", dependencies=[Depends(require_analyst)])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> JSONResponse:
    engine = db.get_engine()
    if engine is None:
        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "database": "not_configured",
                "persistence": "memory",
            },
        )
    ok, err = db.check_database(engine)
    if not ok:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "unavailable", "error": err},
        )
    return JSONResponse(
        status_code=200,
        content={"status": "ready", "database": "ok", "persistence": "postgres"},
    )


@api_router.get("/version")
def api_version() -> dict[str, str | bool | int]:
    return {
        "version": APP_VERSION,
        "service": "sentinel-api",
        "writes_disabled": writes_disabled(),
        "rate_limit_rpm": rate_limit_rpm_configured(),
    }


@api_router.get("/mcp/servers", response_model=McpStatusResponse)
def mcp_servers_status() -> McpStatusResponse:
    """Read-only summary of MCP server names from ``SENTINEL_MCP_CONFIG`` (no secrets)."""
    raw = mcpconfig.summarize_mcp_servers()
    servers = [McpServerEntry(**s) for s in raw["servers"]]
    return McpStatusResponse(
        loaded=raw["loaded"],
        path_configured=raw["path_configured"],
        error=raw["error"],
        server_count=raw["server_count"],
        servers=servers,
    )


@api_router.post("/projects", response_model=CreateProjectResponse, status_code=201)
def create_project(payload: CreateProjectRequest) -> CreateProjectResponse:
    engine = db.get_engine()
    if engine:
        try:
            out = persistence.insert_project(
                engine, name=payload.name, owner_team=payload.owner_team
            )
        except Exception as exc:  # noqa: BLE001
            logutil.emit("project_create_failed", level=30, error=type(exc).__name__)
            raise HTTPException(status_code=500, detail="Failed to create project") from exc
        logutil.emit("project_created", project_id=out.id)
        return out
    project_id = str(uuid4())
    row = {
        "id": project_id,
        "name": payload.name,
        "owner_team": payload.owner_team,
    }
    _mem_projects[project_id] = row
    persistence.register_memory_scope(project_id)
    logutil.emit("project_created", project_id=project_id, persistence="memory")
    return CreateProjectResponse(**row)


@api_router.get("/projects", response_model=ProjectsListResponse)
def list_projects_endpoint() -> ProjectsListResponse:
    engine = db.get_engine()
    if engine:
        rows = persistence.list_projects(engine)
        return ProjectsListResponse(projects=[CreateProjectResponse(**r) for r in rows])
    ordered = sorted(_mem_projects.values(), key=lambda r: r["name"])
    return ProjectsListResponse(projects=[CreateProjectResponse(**r) for r in ordered])


@api_router.get("/projects/{project_id}")
def get_project(project_id: UUID) -> dict:
    engine = db.get_engine()
    if engine:
        row = persistence.fetch_project(engine, project_id)
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
        return row
    key = str(project_id)
    project = _mem_projects.get(key)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@api_router.get("/projects/{project_id}/surface")
def get_surface(project_id: UUID) -> dict:
    engine = db.get_engine()
    if engine:
        if not persistence.project_exists(engine, project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        return persistence.fetch_surface(engine, project_id)
    key = str(project_id)
    if key not in _mem_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    ep_map = _mem_endpoints.get(key, {})
    endpoints = sorted(ep_map.values(), key=lambda e: (e["route_pattern"], e["method"]))
    return {
        "project_id": key,
        "endpoints": endpoints,
        "parameters": [],
        "auth_contexts": [],
    }


@api_router.get(
    "/projects/{project_id}/hypotheses",
    response_model=HypothesisListResponse,
)
def list_project_hypotheses(project_id: UUID) -> HypothesisListResponse:
    key = str(project_id)
    engine = db.get_engine()
    if engine:
        if not persistence.project_exists(engine, project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        rows = persistence.list_hypotheses_for_project(engine, project_id)
        return HypothesisListResponse(
            project_id=key,
            hypotheses=[HypothesisListItem.model_validate(r) for r in rows],
        )
    if key not in _mem_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    rows = [h for h in _mem_hypotheses.values() if h["project_id"] == key]
    rows.sort(
        key=lambda h: h.get("created_at") or datetime(1970, 1, 1, tzinfo=UTC),
        reverse=True,
    )
    return HypothesisListResponse(
        project_id=key,
        hypotheses=[HypothesisListItem.model_validate(h) for h in rows],
    )


@api_router.get(
    "/projects/{project_id}/findings",
    response_model=FindingsListResponse,
)
def list_project_findings(project_id: UUID) -> FindingsListResponse:
    key = str(project_id)
    engine = db.get_engine()
    if engine:
        if not persistence.project_exists(engine, project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        rows = persistence.list_findings_for_project(engine, project_id)
        return FindingsListResponse(
            project_id=key,
            findings=[FindingListItem.model_validate(r) for r in rows],
        )
    if key not in _mem_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    rows = list(_mem_findings.get(key, []))
    return FindingsListResponse(
        project_id=key,
        findings=[FindingListItem.model_validate(r) for r in rows],
    )


@api_router.get(
    "/projects/{project_id}/evidence",
    response_model=EvidenceListResponse,
)
def list_project_evidence(project_id: UUID) -> EvidenceListResponse:
    key = str(project_id)
    engine = db.get_engine()
    if engine:
        if not persistence.project_exists(engine, project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        rows = persistence.list_evidence_bundles(engine, project_id)
        return EvidenceListResponse(
            project_id=key,
            bundles=[EvidenceBundleItem.model_validate(r) for r in rows],
        )
    if key not in _mem_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    rows = list(_mem_evidence.get(key, []))
    return EvidenceListResponse(
        project_id=key,
        bundles=[EvidenceBundleItem.model_validate(r) for r in rows],
    )


@api_router.post(
    "/projects/{project_id}/evidence",
    status_code=201,
    response_model=EvidenceCreatedResponse,
)
def register_evidence_bundle(
    project_id: UUID,
    body: RegisterEvidenceRequest,
) -> EvidenceCreatedResponse:
    storage_key = body.storage_key.strip()
    if not storage_key or "\n" in storage_key or "\r" in storage_key:
        raise HTTPException(status_code=422, detail="Invalid storage_key")
    key = str(project_id)
    engine = db.get_engine()
    if engine:
        if not persistence.project_exists(engine, project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        ensure_project_scope_allows_writes(engine, project_id)
        eid = persistence.insert_evidence_bundle(
            engine,
            project_id,
            storage_key=storage_key,
            summary=body.summary,
        )
        logutil.emit("evidence_registered", project_id=key, evidence_id=eid)
        return EvidenceCreatedResponse(id=eid)
    if key not in _mem_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_scope_allows_writes(None, project_id)
    eid = _memory_append_evidence(key, storage_key, body.summary)
    logutil.emit("evidence_registered", project_id=key, evidence_id=eid, persistence="memory")
    return EvidenceCreatedResponse(id=eid)


@api_router.post("/sync/requests", status_code=202)
def sync_requests(payload: RequestSyncPayload) -> dict:
    engine = db.get_engine()
    if engine:
        if not persistence.project_exists(engine, payload.project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        ensure_project_scope_allows_writes(engine, payload.project_id)
        n = persistence.insert_caido_requests(engine, payload.project_id, payload.requests)
        logutil.emit(
            "sync_requests",
            project_id=str(payload.project_id),
            received=n,
        )
        return {"accepted": True, "received": n}
    key = str(payload.project_id)
    if key not in _mem_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_scope_allows_writes(None, payload.project_id)
    _memory_merge_request_items(key, payload.requests)
    logutil.emit(
        "sync_requests",
        project_id=key,
        received=len(payload.requests),
        persistence="memory",
    )
    return {"accepted": True, "received": len(payload.requests)}


@api_router.post("/sync/findings", status_code=202)
def sync_findings(payload: FindingSyncPayload) -> dict:
    engine = db.get_engine()
    if engine:
        if not persistence.project_exists(engine, payload.project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        ensure_project_scope_allows_writes(engine, payload.project_id)
        n = persistence.insert_findings(engine, payload.project_id, payload.findings)
        logutil.emit("sync_findings", project_id=str(payload.project_id), received=n)
        return {"accepted": True, "received": n}
    key = str(payload.project_id)
    if key not in _mem_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_scope_allows_writes(None, payload.project_id)
    _memory_append_findings(key, payload.findings)
    logutil.emit(
        "sync_findings",
        project_id=key,
        received=len(payload.findings),
        persistence="memory",
    )
    return {"accepted": True, "received": len(payload.findings)}


@api_router.post("/hypotheses/generate", status_code=202)
def generate_hypotheses(payload: HypothesisGenerationRequest) -> HypothesisGenerateAccepted:
    count = min(payload.max_results, 10)
    hypothesis_ids: list[str] = []
    engine = db.get_engine()
    if engine:
        if not persistence.project_exists(engine, payload.project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        ensure_project_scope_allows_writes(engine, payload.project_id)
        for _ in range(count):
            hypothesis_ids.append(persistence.insert_hypothesis_stub(engine, payload.project_id))
        logutil.emit(
            "hypotheses_generate",
            project_id=str(payload.project_id),
            count=len(hypothesis_ids),
        )
        return HypothesisGenerateAccepted(
            project_id=str(payload.project_id),
            hypothesis_ids=hypothesis_ids,
        )
    key = str(payload.project_id)
    if key not in _mem_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    ensure_project_scope_allows_writes(None, payload.project_id)
    for _ in range(count):
        hid = str(uuid4())
        now = datetime.now(UTC)
        _mem_hypotheses[hid] = {
            "id": hid,
            "project_id": key,
            "title": "Hypothesis generation requested",
            "bug_class": "pending",
            "status": "queued",
            "priority_score": 0.5,
            "confidence_score": 0.5,
            "created_at": now,
        }
        hypothesis_ids.append(hid)
    logutil.emit(
        "hypotheses_generate",
        project_id=key,
        count=len(hypothesis_ids),
        persistence="memory",
    )
    return HypothesisGenerateAccepted(
        project_id=key,
        hypothesis_ids=hypothesis_ids,
    )


@api_router.post(
    "/hypotheses/{hypothesis_id}/approve",
    response_model=HypothesisApproveResponse,
)
def approve_hypothesis(hypothesis_id: UUID) -> HypothesisApproveResponse:
    hid = str(hypothesis_id)
    engine = db.get_engine()
    if engine:
        pid = persistence.fetch_hypothesis_project_id(engine, hypothesis_id)
        if pid is None:
            raise HTTPException(status_code=404, detail="Hypothesis not found")
        ensure_project_scope_allows_writes(engine, pid)
        if persistence.approve_hypothesis(engine, hypothesis_id):
            logutil.emit("hypothesis_approved", hypothesis_id=hid)
            return HypothesisApproveResponse(hypothesis_id=hid, status="approved")
        raise HTTPException(
            status_code=409,
            detail="Hypothesis not in queued state or not found",
        )
    row = _mem_hypotheses.get(hid)
    if not row:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    ensure_project_scope_allows_writes(None, UUID(row["project_id"]))
    if row.get("status") != "queued":
        raise HTTPException(
            status_code=409,
            detail="Hypothesis not in queued state",
        )
    row["status"] = "approved"
    logutil.emit("hypothesis_approved", hypothesis_id=hid, persistence="memory")
    return HypothesisApproveResponse(hypothesis_id=hid, status="approved")


@api_router.post(
    "/hypotheses/{hypothesis_id}/reject",
    response_model=HypothesisRejectResponse,
)
def reject_hypothesis(hypothesis_id: UUID) -> HypothesisRejectResponse:
    hid = str(hypothesis_id)
    engine = db.get_engine()
    if engine:
        pid = persistence.fetch_hypothesis_project_id(engine, hypothesis_id)
        if pid is None:
            raise HTTPException(status_code=404, detail="Hypothesis not found")
        ensure_project_scope_allows_writes(engine, pid)
        if persistence.reject_hypothesis(engine, hypothesis_id):
            logutil.emit("hypothesis_rejected", hypothesis_id=hid)
            return HypothesisRejectResponse(hypothesis_id=hid)
        raise HTTPException(
            status_code=409,
            detail="Hypothesis not in queued state or not found",
        )
    row = _mem_hypotheses.get(hid)
    if not row:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    ensure_project_scope_allows_writes(None, UUID(row["project_id"]))
    if row.get("status") != "queued":
        raise HTTPException(
            status_code=409,
            detail="Hypothesis not in queued state",
        )
    row["status"] = "rejected"
    logutil.emit("hypothesis_rejected", hypothesis_id=hid, persistence="memory")
    return HypothesisRejectResponse(hypothesis_id=hid)


@api_router.post("/feedback", status_code=201, response_model=FeedbackCreatedResponse)
def create_feedback(payload: FeedbackRequest) -> FeedbackCreatedResponse:
    engine = db.get_engine()
    if engine:
        try:
            fid = persistence.insert_feedback(engine, payload)
        except Exception as exc:  # noqa: BLE001
            logutil.emit("feedback_failed", level=30, error=type(exc).__name__)
            raise HTTPException(status_code=500, detail="Failed to record feedback") from exc
        logutil.emit(
            "feedback_created",
            feedback_id=fid,
            object_type=payload.object_type,
            feedback_type=payload.feedback_type,
        )
        return FeedbackCreatedResponse(id=fid)
    fid = str(uuid4())
    logutil.emit(
        "feedback_created",
        feedback_id=fid,
        object_type=payload.object_type,
        feedback_type=payload.feedback_type,
        persistence="memory",
    )
    return FeedbackCreatedResponse(id=fid)


def _enqueue_job_body(job_id: str, req: EnqueueJobRequest) -> dict:
    body: dict = {"job_id": job_id, "type": req.type}
    if req.project_id is not None:
        body["project_id"] = str(req.project_id)
    if req.payload is not None:
        body["payload"] = req.payload
    if req.correlation_id:
        body["correlation_id"] = req.correlation_id
    return body


@api_router.post("/jobs", status_code=202, response_model=EnqueueJobResponse)
def enqueue_worker_job(req: EnqueueJobRequest) -> EnqueueJobResponse:
    """LPUSH a JSON job for the worker (ingest, embeddings, ping, noop)."""
    if req.type in ("ingest", "embeddings"):
        project_id = req.project_id
        if project_id is None:
            raise HTTPException(
                status_code=422,
                detail="project_id is required for ingest and embeddings jobs",
            )
        engine = db.get_engine()
        if engine:
            if not persistence.project_exists(engine, project_id):
                raise HTTPException(status_code=404, detail="Project not found")
            ensure_project_scope_allows_writes(engine, project_id)
        else:
            key = str(project_id)
            if key not in _mem_projects:
                raise HTTPException(status_code=404, detail="Project not found")
            ensure_project_scope_allows_writes(None, project_id)

    job_id = str(uuid4())
    try:
        jobqueue.enqueue_job(_enqueue_job_body(job_id, req))
    except jobqueue.RedisNotConfiguredError as exc:
        raise HTTPException(
            status_code=503,
            detail="Job queue unavailable (REDIS_URL not configured)",
        ) from exc
    except RedisError as exc:
        logutil.emit("job_enqueue_failed", level=30, error=type(exc).__name__)
        raise HTTPException(status_code=503, detail="Failed to enqueue job") from exc

    logutil.emit("job_enqueued", job_id=job_id, job_type=req.type)
    return EnqueueJobResponse(job_id=job_id)


app.include_router(api_router)
