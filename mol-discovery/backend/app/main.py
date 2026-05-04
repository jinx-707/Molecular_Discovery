"""
MolDiscovery FastAPI application — production-ready entry point.
Uses lifespan context manager (replaces deprecated on_event).
"""
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.routes import router as discovery_router
from app.api.catalogs import router as catalogs_router
from app.api.experiments import router as experiments_router
from app.api.enzyme import router as enzyme_router
#from app.api.materials import router as materials_router
from app.api.energy import router as energy_router
from app.api.biology import router as biology_router
from app.api.translate import router as translate_router
from app.schemas.validation import ErrorResponse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup + shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ────────────────────────────────────────────────────────
    log.info("=" * 55)
    log.info("  MolDiscovery API starting...")
    log.info("=" * 55)

    # 1. Initialise DB tables
    from app.db.session import init_db
    try:
        init_db()
        log.info("Database tables ready.")
    except Exception as exc:
        log.warning("DB init failed (demo mode active): %s", exc)

    # 2. Verify DB connectivity
    from app.db.session import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log.info("Database connection verified.")
    except Exception as exc:
        log.warning("Database unreachable: %s", exc)

    # 3. Ensure model stubs exist
    model_dir = Path("./models")
    model_dir.mkdir(exist_ok=True)
    existing = list(model_dir.glob("*.pt")) + list(model_dir.glob("*.json"))
    if not existing:
        log.info("No model files found -- creating demo stubs...")
        _create_model_stubs(model_dir)
    else:
        log.info("Models: %d file(s) in %s", len(existing), model_dir)

    # 4. Auto-seed DB if empty
    from app.db.session import SessionLocal
    from app.db.models import Catalyst
    db = SessionLocal()
    try:
        count = db.query(Catalyst).count()
        if count == 0:
            log.info("Database empty -- running seed script...")
            _run_seed()
        else:
            log.info("Database contains %d catalysts.", count)
    except Exception as exc:
        log.warning("Could not check/seed DB: %s", exc)
    finally:
        db.close()

    log.info("Startup complete. Docs: http://localhost:8000/docs")
    log.info("=" * 55)

    yield  # ── application runs ──

    # ── SHUTDOWN ───────────────────────────────────────────────────────
    log.info("Shutting down MolDiscovery API...")
    try:
        from app.db.session import engine
        engine.dispose()
    except Exception:
        pass
    log.info("Shutdown complete.")


def _create_model_stubs(model_dir: Path) -> None:
    stubs = {
        "catalyst_gnn.json": {"version": "demo_v1", "type": "CatalystGNN"},
        "diffusion.json":    {"version": "demo_v1", "type": "DiffusionGenerator"},
    }
    for name, content in stubs.items():
        p = model_dir / name
        if not p.exists():
            p.write_text(json.dumps(content, indent=2))
            log.info("Created model stub: %s", p)


def _run_seed() -> None:
    try:
        from scripts.seed_database import seed_database
        seed_database()
    except Exception as exc:
        log.warning("Auto-seed failed: %s", exc)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MolDiscovery API",
    description="AI Platform for Molecular Discovery in Chemical Catalysis",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "CORS_ORIGINS", [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(discovery_router)
app.include_router(catalogs_router)
app.include_router(experiments_router)
app.include_router(enzyme_router)
#app.include_router(materials_router)
app.include_router(energy_router)
app.include_router(biology_router)
app.include_router(translate_router)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=str(exc.detail),
            detail=f"{request.method} {request.url.path}",
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    log.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc) if os.getenv("DEBUG", "False").lower() == "true" else None,
        ).model_dump(),
    )


# ---------------------------------------------------------------------------
# Root / health
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "MolDiscovery API",
        "version": "2.0.0",
        "status":  "running",
        "docs":    "/docs",
        "endpoints": {
            "discovery":   "POST /api/discovery/start",
            "results":     "GET  /api/discovery/{run_id}/results",
            "status":      "GET  /api/discovery/{run_id}/status",
            "experiments": "POST /api/experiment/log",
            "health":      "GET  /api/model/health",
            "retrain":     "POST /api/model/retrain",
            "catalogs":    "GET  /api/catalogs/catalysts",
            "statistics":  "GET  /api/catalogs/statistics",
        },
    }


@app.get("/health")
async def health():
    from app.db.session import engine
    from sqlalchemy import text

    db_status = "unknown"
    catalyst_count = 0
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
        from app.db.session import SessionLocal
        from app.db.models import Catalyst
        db = SessionLocal()
        try:
            catalyst_count = db.query(Catalyst).count()
        finally:
            db.close()
    except Exception as exc:
        db_status = f"unavailable ({exc})"

    return {
        "status":          "healthy",
        "service":         "backend",
        "database":        db_status,
        "catalyst_count":  catalyst_count,
        "version":         "2.0.0",
    }


# ---------------------------------------------------------------------------
# Dev runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
