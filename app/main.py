from __future__ import annotations

import hmac
import re
import secrets
import time
from contextlib import asynccontextmanager
from pathlib import Path
from threading import RLock
from typing import Annotated

import structlog
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware

from app.ai import GeminiExpectationAgent, build_adk_registry
from app.config import Settings, get_settings
from app.demo import create_demo_case, observe_bill, resolve, verify_credit
from app.domain import AdvanceRequest, ReconciliationCase, TextEvidenceRequest
from app.store import CaseStore, create_store

log = structlog.get_logger()
STATIC_DIR = Path(__file__).parent / "static"
SESSION_RE = re.compile(r"^[A-Za-z0-9_-]{20,64}$")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.store = create_store(settings)
    app.state.expectation_agent = GeminiExpectationAgent(settings)
    app.state.demo_lock = RLock()
    yield


app = FastAPI(
    title="RealityCheck API",
    version="1.0.0",
    description="Evidence-backed personal reality reconciliation powered by Gemini and Google ADK.",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Tasks-Secret"],
)
app.add_middleware(GZipMiddleware, minimum_size=500)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def security_and_trace(request: Request, call_next):
    started = time.perf_counter()
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; connect-src 'self'"
    )
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=86400"
    else:
        response.headers["Cache-Control"] = "no-store"
    log.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round((time.perf_counter() - started) * 1000, 2),
    )
    return response


def store(request: Request) -> CaseStore:
    return request.app.state.store


CaseStoreDep = Annotated[CaseStore, Depends(store)]
TasksSecretHeader = Annotated[str | None, Header()]


def demo_case_id(request: Request, response: Response) -> str:
    session_id = request.cookies.get("rc_session", "")
    if not SESSION_RE.fullmatch(session_id):
        session_id = secrets.token_urlsafe(24)
        settings: Settings = request.app.state.settings
        response.set_cookie(
            "rc_session",
            session_id,
            max_age=86_400,
            httponly=True,
            secure=settings.is_production,
            samesite="strict",
        )
    return f"case_fibermax_demo_{session_id}"


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health(request: Request):
    settings: Settings = request.app.state.settings
    return {
        "status": "ok",
        "service": "realitycheck",
        "version": "1.0.0",
        "model": settings.gemini_model,
        "ai_configured": settings.ai_configured,
        "store": settings.realitycheck_store,
        "provider_mode": settings.provider_mode,
    }


@app.get("/api/agents")
def agents(request: Request):
    return {
        "orchestrator": "realitycheck_fleet",
        "agents": build_adk_registry(request.app.state.settings),
    }


@app.get("/api/cases", response_model=list[ReconciliationCase])
def list_cases(case_store: CaseStoreDep):
    return case_store.list()


@app.get("/api/cases/{case_id}", response_model=ReconciliationCase)
def get_case(case_id: str, case_store: CaseStoreDep):
    case = case_store.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@app.post("/api/contracts/extract")
def extract_contract(payload: TextEvidenceRequest, request: Request):
    contract, mode = request.app.state.expectation_agent.extract(
        payload.filename, payload.text, payload.counterparty_hint
    )
    case = ReconciliationCase(
        title=f"{contract.counterparty}: {contract.subject}", expectation=contract
    )
    case.record(
        "expectation_agent",
        "contract_compiled",
        f"Compiled {len(contract.terms)} measurable terms.",
        [e.id for e in contract.evidence],
        execution_mode=mode,
    )
    request.app.state.store.put(case)
    return {"execution_mode": mode, "case": case}


@app.post("/api/demo/reset", response_model=ReconciliationCase)
def reset_demo(request: Request, response: Response, case_store: CaseStoreDep):
    case_id = demo_case_id(request, response)
    with request.app.state.demo_lock:
        case = create_demo_case(case_id)
        case_store.put(case)
    return case


@app.get("/api/demo/state", response_model=ReconciliationCase)
def demo_state(request: Request, response: Response, case_store: CaseStoreDep):
    case_id = demo_case_id(request, response)
    with request.app.state.demo_lock:
        case = case_store.get(case_id)
        if not case:
            case = create_demo_case(case_id)
            case_store.put(case)
    return case


@app.post("/api/demo/advance", response_model=ReconciliationCase)
def advance_demo(
    payload: AdvanceRequest, request: Request, response: Response, case_store: CaseStoreDep
):
    case_id = demo_case_id(request, response)
    if payload.step not in {"observe", "resolve", "verify"}:
        raise HTTPException(status_code=400, detail="step must be observe, resolve, or verify")

    def transition(case: ReconciliationCase) -> ReconciliationCase:
        if payload.step == "observe":
            return observe_bill(case)
        if payload.step == "resolve":
            return resolve(case, payload.approve)
        return verify_credit(case, demo_time_jump=True)

    with request.app.state.demo_lock:
        return case_store.mutate(case_id, lambda: create_demo_case(case_id), transition)


@app.post("/api/tasks/tick")
def tasks_tick(
    request: Request, case_store: CaseStoreDep, x_tasks_secret: TasksSecretHeader = None
):
    settings: Settings = request.app.state.settings
    if (
        not settings.tasks_shared_secret
        or not x_tasks_secret
        or not hmac.compare_digest(settings.tasks_shared_secret, x_tasks_secret)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid task secret")
    due = [
        case
        for case in case_store.list()
        if case.next_action_at and case.next_action_at.timestamp() <= time.time()
    ]
    recovered = []
    for due_case in due:
        if due_case.status != "monitoring":
            continue
        updated = case_store.mutate(
            due_case.id,
            lambda case=due_case: case,
            lambda case: verify_credit(case),
        )
        if updated.status == "recovered":
            recovered.append(updated.id)
    return {
        "due_cases": [case.id for case in due],
        "recovered_cases": recovered,
        "count": len(due),
    }
