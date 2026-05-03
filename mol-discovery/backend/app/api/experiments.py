"""
Experiments API — log, list, and inspect experimental results.
"""
import io
import uuid
import logging
from datetime import datetime
from typing import Optional, List

import pandas as pd
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Experiment, Discrepancy, Prediction
from app.services.feedback_service import FeedbackService

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/experiments", tags=["experiments"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ExperimentResponse(BaseModel):
    id: str
    candidate_id: Optional[str]
    measured_activity: Optional[float]
    measured_selectivity: Optional[float]
    measured_stability: Optional[int]
    temperature: Optional[float]
    pressure: Optional[float]
    researcher: Optional[str]
    created_at: Optional[str]
    discrepancy_percent: Optional[float] = None
    hypothesis: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/log")
async def log_experiment(
    file:                 Optional[UploadFile] = File(None),
    candidate_id:         Optional[str]   = Form(None),
    measured_activity:    Optional[float] = Form(None),
    measured_selectivity: Optional[float] = Form(None),
    measured_stability:   Optional[int]   = Form(None),
    temperature:          float           = Form(350.0),
    pressure:             float           = Form(1.0),
    researcher:           str             = Form("unknown"),
    db: Session = Depends(get_db),
):
    """Log experimental results from a CSV file or individual form fields."""
    feedback = FeedbackService()

    if file:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode("utf-8")))

        results = []
        for _, row in df.iterrows():
            exp = Experiment(
                id=str(uuid.uuid4()),
                candidate_id=row.get("candidate_id"),
                measured_activity=row.get("activity") or row.get("measured_activity"),
                measured_selectivity=row.get("selectivity") or row.get("measured_selectivity", 0),
                measured_stability=int(row.get("stability") or row.get("measured_stability") or 0),
                temperature=float(row.get("temperature", temperature)),
                pressure=float(row.get("pressure", pressure)),
                researcher=str(row.get("researcher", researcher)),
            )
            db.add(exp)
            db.flush()
            disc = feedback.analyze_experiment(exp.id)
            results.append({"experiment_id": exp.id, "discrepancy": disc})

        db.commit()
        return {"status": "success", "logged": len(results), "results": results}

    if candidate_id and measured_activity is not None:
        exp = Experiment(
            id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            measured_activity=measured_activity,
            measured_selectivity=measured_selectivity or 0.0,
            measured_stability=measured_stability or 0,
            temperature=temperature,
            pressure=pressure,
            researcher=researcher,
        )
        db.add(exp)
        db.commit()
        db.refresh(exp)

        disc = feedback.analyze_experiment(exp.id)
        return {
            "status":           "success",
            "experiment_id":    exp.id,
            "discrepancy":      disc,
            "needs_retraining": disc > 0.2,
        }

    raise HTTPException(
        status_code=400,
        detail="Provide either a CSV file or candidate_id + measured_activity.",
    )


@router.get("/", response_model=List[ExperimentResponse])
def list_experiments(
    skip:       int            = 0,
    limit:      int            = 50,
    researcher: Optional[str]  = None,
    db: Session = Depends(get_db),
):
    """List all experiments, newest first."""
    query = db.query(Experiment)
    if researcher:
        query = query.filter(Experiment.researcher == researcher)

    rows = query.order_by(Experiment.created_at.desc()).offset(skip).limit(limit).all()

    results = []
    for exp in rows:
        disc = (
            db.query(Discrepancy)
            .filter(Discrepancy.experiment_id == exp.id)
            .first()
        )
        results.append(ExperimentResponse(
            id=str(exp.id),
            candidate_id=str(exp.candidate_id) if exp.candidate_id else None,
            measured_activity=exp.measured_activity,
            measured_selectivity=exp.measured_selectivity,
            measured_stability=exp.measured_stability,
            temperature=exp.temperature,
            pressure=exp.pressure,
            researcher=exp.researcher,
            created_at=exp.created_at.isoformat() if exp.created_at else None,
            discrepancy_percent=disc.discrepancy_percent if disc else None,
            hypothesis=disc.root_cause_hypothesis if disc else None,
        ))
    return results


@router.get("/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    """Get a single experiment with its discrepancy analysis."""
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    disc = (
        db.query(Discrepancy)
        .filter(Discrepancy.experiment_id == experiment_id)
        .first()
    )

    # Also fetch the matching prediction for comparison
    pred = None
    if exp.candidate_id:
        pred = (
            db.query(Prediction)
            .filter(Prediction.candidate_id == exp.candidate_id)
            .order_by(Prediction.created_at.desc())
            .first()
        )

    return ExperimentResponse(
        id=str(exp.id),
        candidate_id=str(exp.candidate_id) if exp.candidate_id else None,
        measured_activity=exp.measured_activity,
        measured_selectivity=exp.measured_selectivity,
        measured_stability=exp.measured_stability,
        temperature=exp.temperature,
        pressure=exp.pressure,
        researcher=exp.researcher,
        created_at=exp.created_at.isoformat() if exp.created_at else None,
        discrepancy_percent=disc.discrepancy_percent if disc else None,
        hypothesis=disc.root_cause_hypothesis if disc else None,
    )
