"""
Energy Profile API
==================
GET  /api/energy/{candidate_id}/{reaction_id}  — fetch or compute profile
POST /api/energy/compute                        — trigger background computation
GET  /api/energy/status                         — calculator availability
GET  /api/model/drift                           — drift report
GET  /api/model/drift/history                   — past drift events
POST /api/model/retrain/async                   — async retraining
GET  /api/model/versions                        — model version history
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from app.simulation.energy_reaction import ReactionEnergyService
from app.services.feedback_service import FeedbackService

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["energy", "model"])

# Lazy singletons
_energy_svc:    Optional[ReactionEnergyService] = None
_feedback_svc:  Optional[FeedbackService]       = None


def _es() -> ReactionEnergyService:
    global _energy_svc
    if _energy_svc is None:
        _energy_svc = ReactionEnergyService()
    return _energy_svc


def _fs() -> FeedbackService:
    global _feedback_svc
    if _feedback_svc is None:
        _feedback_svc = FeedbackService()
    return _feedback_svc


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ComputeRequest(BaseModel):
    candidate_id:     str
    reaction_smiles:  str
    catalyst_name:    str = ""
    force_recompute:  bool = False


# ---------------------------------------------------------------------------
# Energy endpoints
# ---------------------------------------------------------------------------

@router.get("/energy/{candidate_id}/{reaction_id}")
async def get_energy_profile(
    candidate_id: str,
    reaction_id:  str,
    reaction_smiles: str = Query("CCO>>CC=O", description="Reaction SMILES (R>>P)"),
    catalyst_name:   str = Query("", description="Catalyst name for display"),
    force:           bool = Query(False, description="Force recompute even if cached"),
) -> Dict[str, Any]:
    """
    Fetch (or compute) the reaction energy profile for a candidate.

    Returns:
      reactant_energy, product_energy, transition_state_energy,
      activation_energy_eV, reaction_energy_eV,
      neb_energies (list of floats for the reaction coordinate plot),
      reaction_coordinate (list of 0–1 values),
      calculator, cached
    """
    try:
        profile = _es().get_profile(
            catalyst_id=candidate_id,
            reaction_smiles=reaction_smiles,
            catalyst_name=catalyst_name,
            force_recompute=force,
        )
        return profile
    except Exception as exc:
        log.error("get_energy_profile failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/energy/compute")
async def compute_energy_profile(
    body:               ComputeRequest,
    background_tasks:   BackgroundTasks,
) -> Dict[str, Any]:
    """
    Trigger energy profile computation in the background.
    Returns immediately; poll GET /api/energy/{id}/{rxn} for results.
    """
    def _run():
        _es().get_profile(
            catalyst_id=body.candidate_id,
            reaction_smiles=body.reaction_smiles,
            catalyst_name=body.catalyst_name,
            force_recompute=body.force_recompute,
        )

    background_tasks.add_task(_run)
    return {
        "status":        "queued",
        "candidate_id":  body.candidate_id,
        "message":       "Energy profile computation started. Poll GET /api/energy/{id}/{rxn}.",
    }


@router.get("/energy/status")
async def energy_status() -> Dict[str, Any]:
    """Check which energy calculator is available."""
    return _es().get_status()


# ---------------------------------------------------------------------------
# Drift endpoints
# ---------------------------------------------------------------------------

@router.get("/model/drift")
async def get_drift_report(
    window_days: int = Query(30, ge=1, le=365),
) -> Dict[str, Any]:
    """
    Run drift detection comparing the last *window_days* of experiments
    against the historical reference dataset.
    """
    try:
        return _fs().check_drift(window_days=window_days)
    except Exception as exc:
        log.error("drift check failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/model/drift/history")
async def get_drift_history(
    limit: int = Query(10, ge=1, le=100),
) -> Dict[str, Any]:
    """Return recent drift events from the audit log."""
    try:
        events = _fs().get_drift_history(limit=limit)
        return {"events": events, "count": len(events)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Async retraining
# ---------------------------------------------------------------------------

@router.post("/model/retrain/async")
async def retrain_async(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Trigger model retraining as a background task.
    Returns immediately; check /api/model/health for retraining_in_progress.
    """
    return _fs().retrain_async(background_tasks)


# ---------------------------------------------------------------------------
# Model version history
# ---------------------------------------------------------------------------

@router.get("/model/versions")
async def get_model_versions(
    limit: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """Return model version history with validation metrics."""
    try:
        from app.db.session import SessionLocal
        from app.db.models import ModelMetadata

        db = SessionLocal()
        try:
            rows = (
                db.query(ModelMetadata)
                .order_by(ModelMetadata.created_at.desc())
                .limit(limit)
                .all()
            )
            versions = [
                {
                    "version":       r.model_version,
                    "samples_used":  r.samples_used,
                    "epochs":        r.epochs,
                    "val_mae":       r.val_mae,
                    "val_r2":        r.val_r2,
                    "is_production": r.is_production,
                    "promoted_at":   r.promoted_at.isoformat() if r.promoted_at else None,
                    "created_at":    r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
            return {"versions": versions, "count": len(versions)}
        finally:
            db.close()
    except Exception as exc:
        log.error("get_model_versions failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
