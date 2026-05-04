"""
API routes — all endpoints under /api prefix.
"""
import io
import logging
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Form, HTTPException, Query, UploadFile, File

from app.services.discovery_service import DiscoveryService
from app.services.feedback_service import FeedbackService
from app.data.ingestor import DataIngestor
from app.schemas.validation import ReactionInput
from app.services.sarvam_service import translate_with_glossary

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["discovery"])

# ---------------------------------------------------------------------------
# Lazy singletons — instantiated on first request so tests can set
# DATABASE_URL before any DB session is created.
# ---------------------------------------------------------------------------
_discovery_service: Optional[DiscoveryService] = None
_feedback_service:  Optional[FeedbackService]  = None
_ingestor:          Optional[DataIngestor]      = None


def _ds() -> DiscoveryService:
    global _discovery_service
    if _discovery_service is None:
        _discovery_service = DiscoveryService()
    return _discovery_service


def _fs() -> FeedbackService:
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service


def _ing() -> DataIngestor:
    global _ingestor
    if _ingestor is None:
        _ingestor = DataIngestor()
    return _ingestor


# ---------------------------------------------------------------------------
# Discovery endpoints
# ---------------------------------------------------------------------------

@router.post("/discovery/start")
async def start_discovery(
    body: ReactionInput,
    lang: str = Query("en", description="Response language: 'en' or 'kn'"),
):
    """Start a new catalyst discovery run. Pass ?lang=kn for Kannada output."""
    try:
        result = await _ds().run_discovery(
            reaction=body.reaction,
            constraints=body.constraints,
            user_id=body.user_id,
        )
        # Translate dynamic candidate fields when Kannada is requested
        if lang == "kn" and isinstance(result, dict) and "candidates" in result:
            for c in result["candidates"]:
                if c.get("name"):
                    c["name_kn"] = translate_with_glossary(c["name"])
                if c.get("details"):
                    c["details_kn"] = translate_with_glossary(c["details"])
        return result
    except Exception as exc:
        log.error("start_discovery error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/discovery/{run_id}/results")
async def get_results(run_id: str):
    """Get results of a completed discovery run."""
    result = _ds().get_results(run_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/discovery/{run_id}/status")
async def get_status(run_id: str):
    """Check the status of a discovery run."""
    from app.db.session import SessionLocal
    from app.db.models import DiscoveryRun

    db = SessionLocal()
    try:
        run = db.query(DiscoveryRun).filter(DiscoveryRun.id == run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return {
            "run_id":     run_id,
            "status":     run.status,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Experiment logging
# ---------------------------------------------------------------------------

@router.post("/experiment/log")
async def log_experiment(
    file:         Optional[UploadFile] = File(None),
    candidate_id: Optional[str]   = Form(None),
    activity:     Optional[float] = Form(None),
    selectivity:  Optional[float] = Form(None),
    stability:    Optional[int]   = Form(None),
    temperature:  Optional[float] = Form(350.0),
    pressure:     Optional[float] = Form(1.0),
    researcher:   str             = Form("unknown"),
):
    """
    Log experimental results.
    Accepts either a CSV file upload or individual form fields.
    """
    if file:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        count = _ing().ingest_csv_from_dataframe(df)
        _fs().analyze_new_experiments()
        return {"status": "success", "experiments_logged": count}

    if candidate_id and activity is not None:
        exp_data = {
            "candidate_id": candidate_id,
            "activity":     activity,
            "selectivity":  selectivity,
            "stability":    stability or 0,
            "temperature":  temperature,
            "pressure":     pressure,
            "researcher":   researcher,
        }
        exp_id      = _ing().store_experiment(exp_data)
        discrepancy = _fs().analyze_experiment(exp_id)
        return {
            "status":        "success",
            "experiment_id": exp_id,
            "discrepancy":   discrepancy,
        }

    raise HTTPException(
        status_code=400,
        detail="Provide either a CSV file or candidate_id + activity fields.",
    )


# ---------------------------------------------------------------------------
# Model health & retraining
# ---------------------------------------------------------------------------

@router.get("/model/health")
async def model_health():
    """Return model performance dashboard data."""
    return _fs().get_model_health()


@router.post("/model/retrain")
async def trigger_retraining():
    """Manually trigger model retraining."""
    return _fs().retrain_models()


# ---------------------------------------------------------------------------
# Catalyst search
# ---------------------------------------------------------------------------

@router.get("/catalysts/search")
async def search_catalysts(query: str, limit: int = 20):
    """Search for known catalysts by reaction or name."""
    results = _ing().fetch_known_catalysts(query, limit=limit)
    return {"results": results, "count": len(results)}
