"""
Synthetic Biology API
=====================
POST /api/biology/pathway/design      — full pathway design
GET  /api/biology/pathway/types       — available pathway types
GET  /api/biology/microorganisms      — host organism catalogue
POST /api/biology/enzyme/mutations    — rule-based mutation suggestions
POST /api/biology/enzyme/thermostability — predict Tm after mutations
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.pathway_service import (
    PathwayDesignerService,
    EnzymeEngineeringService,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/biology", tags=["synthetic-biology"])

# Lazy singletons
_pathway_svc: Optional[PathwayDesignerService]    = None
_enzyme_svc:  Optional[EnzymeEngineeringService]  = None


def _ps() -> PathwayDesignerService:
    global _pathway_svc
    if _pathway_svc is None:
        _pathway_svc = PathwayDesignerService()
    return _pathway_svc


def _es() -> EnzymeEngineeringService:
    global _enzyme_svc
    if _enzyme_svc is None:
        _enzyme_svc = EnzymeEngineeringService()
    return _enzyme_svc


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class PathwayRequest(BaseModel):
    target_reaction:     str            = Field(..., min_length=3)
    organism_preference: Optional[str] = None


class MutationRequest(BaseModel):
    sequence:        str = Field(..., min_length=5, max_length=2000,
                                 description="Amino-acid sequence (single-letter codes)")
    target_property: str = Field("thermostability",
                                 description="thermostability | activity | selectivity")
    top_k:           int = Field(10, ge=1, le=50)


class ThermostabilityRequest(BaseModel):
    sequence:  str
    mutations: List[Dict[str, Any]]


# ---------------------------------------------------------------------------
# Pathway endpoints
# ---------------------------------------------------------------------------

@router.post("/pathway/design")
async def design_pathway(request: PathwayRequest) -> Dict[str, Any]:
    """
    Design a complete metabolic pathway for a target reaction.

    Returns recommended microorganism, enzyme list with kinetics,
    genetic modifications (CRISPR/KO/OE), predicted yield,
    bottleneck analysis, and flux distribution.
    """
    try:
        return _ps().design_pathway(
            request.target_reaction,
            request.organism_preference,
        )
    except Exception as exc:
        log.error("design_pathway failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/pathway/types")
async def get_pathway_types() -> Dict[str, Any]:
    """List all supported pathway types."""
    return {"pathways": _ps().get_pathway_types()}


@router.get("/microorganisms")
async def list_microorganisms() -> Dict[str, Any]:
    """List available host microorganisms with capability profiles."""
    return {"microorganisms": _ps().get_microorganisms()}


# ---------------------------------------------------------------------------
# Enzyme engineering endpoints
# ---------------------------------------------------------------------------

@router.post("/enzyme/mutations")
async def suggest_mutations(request: MutationRequest) -> Dict[str, Any]:
    """
    Suggest point mutations to improve enzyme properties using rule-based
    heuristics.  For ML-based LLR scoring, use POST /api/enzyme/suggest.
    """
    try:
        mutations = _es().suggest_mutations(
            request.sequence,
            request.target_property,
            request.top_k,
        )
        return {
            "sequence_length":          len(request.sequence),
            "target_property":          request.target_property,
            "mutations":                mutations,
            "count":                    len(mutations),
            "predicted_thermostability": _es().predict_thermostability(
                request.sequence, mutations
            ),
        }
    except Exception as exc:
        log.error("suggest_mutations failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/enzyme/thermostability")
async def predict_thermostability(request: ThermostabilityRequest) -> Dict[str, Any]:
    """Predict enzyme thermostability after applying a set of mutations."""
    try:
        tm = _es().predict_thermostability(request.sequence, request.mutations)
        return {
            "sequence_length":          len(request.sequence),
            "n_mutations":              len(request.mutations),
            "predicted_thermostability": tm,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
