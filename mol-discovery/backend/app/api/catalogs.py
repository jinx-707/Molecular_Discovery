"""
Catalog API — CRUD for the catalyst library.
"""
import uuid
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Catalyst

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/catalogs", tags=["catalogs"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class CatalystCreate(BaseModel):
    name: str
    composition: dict = {}
    catalyst_type: Optional[str] = None
    reaction_target: Optional[str] = None
    reported_activity: Optional[float] = None
    reported_selectivity: Optional[float] = None
    reported_stability: Optional[int] = None
    source: str = "user_upload"


class CatalystResponse(BaseModel):
    id: str
    name: str
    composition: dict
    catalyst_type: Optional[str]
    reaction_target: Optional[str]
    reported_activity: Optional[float]
    reported_selectivity: Optional[float]
    reported_stability: Optional[int]
    source: Optional[str]
    created_at: Optional[str]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/catalysts", response_model=List[CatalystResponse])
def list_catalysts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    reaction: Optional[str] = None,
    catalyst_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List catalysts with optional filters."""
    query = db.query(Catalyst)
    if reaction:
        query = query.filter(Catalyst.reaction_target.ilike(f"%{reaction}%"))
    if catalyst_type:
        query = query.filter(Catalyst.catalyst_type == catalyst_type)

    rows = query.offset(skip).limit(limit).all()
    return [
        CatalystResponse(
            id=str(r.id),
            name=r.name,
            composition=r.composition or {},
            catalyst_type=r.catalyst_type,
            reaction_target=r.reaction_target,
            reported_activity=r.reported_activity,
            reported_selectivity=r.reported_selectivity,
            reported_stability=r.reported_stability,
            source=r.source,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in rows
    ]


@router.get("/catalysts/{catalyst_id}", response_model=CatalystResponse)
def get_catalyst(catalyst_id: str, db: Session = Depends(get_db)):
    """Get a specific catalyst by ID."""
    cat = db.query(Catalyst).filter(Catalyst.id == catalyst_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Catalyst not found")
    return CatalystResponse(
        id=str(cat.id),
        name=cat.name,
        composition=cat.composition or {},
        catalyst_type=cat.catalyst_type,
        reaction_target=cat.reaction_target,
        reported_activity=cat.reported_activity,
        reported_selectivity=cat.reported_selectivity,
        reported_stability=cat.reported_stability,
        source=cat.source,
        created_at=cat.created_at.isoformat() if cat.created_at else None,
    )


@router.post("/catalysts", response_model=CatalystResponse, status_code=201)
def create_catalyst(body: CatalystCreate, db: Session = Depends(get_db)):
    """Add a new catalyst to the catalog."""
    cat = Catalyst(
        id=str(uuid.uuid4()),
        name=body.name,
        composition=body.composition,
        catalyst_type=body.catalyst_type,
        reaction_target=body.reaction_target,
        reported_activity=body.reported_activity,
        reported_selectivity=body.reported_selectivity,
        reported_stability=body.reported_stability,
        source=body.source,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return CatalystResponse(
        id=str(cat.id),
        name=cat.name,
        composition=cat.composition or {},
        catalyst_type=cat.catalyst_type,
        reaction_target=cat.reaction_target,
        reported_activity=cat.reported_activity,
        reported_selectivity=cat.reported_selectivity,
        reported_stability=cat.reported_stability,
        source=cat.source,
        created_at=cat.created_at.isoformat() if cat.created_at else None,
    )


@router.delete("/catalysts/{catalyst_id}", status_code=204)
def delete_catalyst(catalyst_id: str, db: Session = Depends(get_db)):
    """Remove a catalyst from the catalog."""
    cat = db.query(Catalyst).filter(Catalyst.id == catalyst_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Catalyst not found")
    db.delete(cat)
    db.commit()


@router.get("/statistics")
def get_catalog_statistics(db: Session = Depends(get_db)):
    """Summary statistics for the catalog."""
    total = db.query(Catalyst).count()

    by_type = {}
    for t in ["heterogeneous", "homogeneous", "enzyme"]:
        by_type[t] = db.query(Catalyst).filter(Catalyst.catalyst_type == t).count()

    by_source = {}
    for s in ["open_catalyst", "materials_project", "user_upload", "ai_generated", "synthetic_demo"]:
        by_source[s] = db.query(Catalyst).filter(Catalyst.source == s).count()

    return {
        "total_catalysts": total,
        "by_type":         by_type,
        "by_source":       by_source,
    }
