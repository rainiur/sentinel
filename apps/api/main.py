from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

import db
import logutil
import persistence
from schemas import (
    CreateProjectRequest,
    CreateProjectResponse,
    FeedbackCreatedResponse,
    FeedbackRequest,
    FindingSyncPayload,
    HypothesisApproveResponse,
    HypothesisGenerateAccepted,
    HypothesisGenerationRequest,
    RequestSyncPayload,
)

load_dotenv()

APP_VERSION = "0.1.0"

_mem_projects: dict[str, dict] = {}
_mem_hypotheses: dict[str, dict] = {}


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


@app.get("/api/version")
def api_version() -> dict[str, str]:
    return {"version": APP_VERSION, "service": "sentinel-api"}


@app.post("/api/projects", response_model=CreateProjectResponse, status_code=201)
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
    logutil.emit("project_created", project_id=project_id, persistence="memory")
    return CreateProjectResponse(**row)


@app.get("/api/projects/{project_id}")
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


@app.get("/api/projects/{project_id}/surface")
def get_surface(project_id: UUID) -> dict:
    engine = db.get_engine()
    if engine:
        if not persistence.project_exists(engine, project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        return persistence.fetch_surface(engine, project_id)
    key = str(project_id)
    if key not in _mem_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "project_id": key,
        "endpoints": [],
        "parameters": [],
        "auth_contexts": [],
    }


@app.post("/api/sync/requests", status_code=202)
def sync_requests(payload: RequestSyncPayload) -> dict:
    engine = db.get_engine()
    if engine:
        if not persistence.project_exists(engine, payload.project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        n = persistence.insert_caido_requests(
            engine, payload.project_id, payload.requests
        )
        logutil.emit(
            "sync_requests",
            project_id=str(payload.project_id),
            received=n,
        )
        return {"accepted": True, "received": n}
    key = str(payload.project_id)
    if key not in _mem_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    logutil.emit(
        "sync_requests",
        project_id=key,
        received=len(payload.requests),
        persistence="memory",
    )
    return {"accepted": True, "received": len(payload.requests)}


@app.post("/api/sync/findings", status_code=202)
def sync_findings(payload: FindingSyncPayload) -> dict:
    engine = db.get_engine()
    if engine:
        if not persistence.project_exists(engine, payload.project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        n = persistence.insert_findings(engine, payload.project_id, payload.findings)
        logutil.emit("sync_findings", project_id=str(payload.project_id), received=n)
        return {"accepted": True, "received": n}
    key = str(payload.project_id)
    if key not in _mem_projects:
        raise HTTPException(status_code=404, detail="Project not found")
    logutil.emit(
        "sync_findings",
        project_id=key,
        received=len(payload.findings),
        persistence="memory",
    )
    return {"accepted": True, "received": len(payload.findings)}


@app.post("/api/hypotheses/generate", status_code=202)
def generate_hypotheses(payload: HypothesisGenerationRequest) -> HypothesisGenerateAccepted:
    count = min(payload.max_results, 10)
    hypothesis_ids: list[str] = []
    engine = db.get_engine()
    if engine:
        if not persistence.project_exists(engine, payload.project_id):
            raise HTTPException(status_code=404, detail="Project not found")
        for _ in range(count):
            hypothesis_ids.append(
                persistence.insert_hypothesis_stub(engine, payload.project_id)
            )
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
    for _ in range(count):
        hid = str(uuid4())
        _mem_hypotheses[hid] = {"id": hid, "project_id": key, "status": "queued"}
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


@app.post(
    "/api/hypotheses/{hypothesis_id}/approve",
    response_model=HypothesisApproveResponse,
)
def approve_hypothesis(hypothesis_id: UUID) -> HypothesisApproveResponse:
    hid = str(hypothesis_id)
    engine = db.get_engine()
    if engine:
        if persistence.approve_hypothesis(engine, hypothesis_id):
            logutil.emit("hypothesis_approved", hypothesis_id=hid)
            return HypothesisApproveResponse(hypothesis_id=hid)
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    row = _mem_hypotheses.get(hid)
    if not row:
        raise HTTPException(status_code=404, detail="Hypothesis not found")
    row["status"] = "approved"
    logutil.emit("hypothesis_approved", hypothesis_id=hid, persistence="memory")
    return HypothesisApproveResponse(hypothesis_id=hid)


@app.post("/api/feedback", status_code=201, response_model=FeedbackCreatedResponse)
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
