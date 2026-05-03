"""
Enzyme Engineering API
======================
POST /api/enzyme/llr          — LLR scores for specific mutations
POST /api/enzyme/suggest      — AI-suggested beneficial mutations
POST /api/enzyme/score-variant — Score a full variant vs wild-type
POST /api/enzyme/grna         — CRISPR gRNA design for a target gene
GET  /api/enzyme/flux         — FBA flux distribution
POST /api/enzyme/knockouts    — Gene knockout targets
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ml.enzyme_predictor import EnzymePredictor
from app.simulation.flux import PathwayDesigner

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/enzyme", tags=["enzyme"])

# Lazy singletons
_predictor: Optional[EnzymePredictor] = None
_designer:  Optional[PathwayDesigner]  = None


def _ep() -> EnzymePredictor:
    global _predictor
    if _predictor is None:
        _predictor = EnzymePredictor()
    return _predictor


def _pd() -> PathwayDesigner:
    global _designer
    if _designer is None:
        _designer = PathwayDesigner()
    return _designer


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class MutationSpec(BaseModel):
    position: int = Field(..., ge=0, description="0-indexed position in sequence")
    wt:       str = Field(..., min_length=1, max_length=1)
    mt:       str = Field(..., min_length=1, max_length=1)


class LLRRequest(BaseModel):
    sequence:  str              = Field(..., min_length=5, max_length=2000)
    mutations: List[MutationSpec]


class SuggestRequest(BaseModel):
    sequence: str = Field(..., min_length=5, max_length=2000)
    top_k:    int = Field(10, ge=1, le=50)
    min_llr:  float = Field(0.3, ge=-5.0, le=5.0)


class VariantRequest(BaseModel):
    wt_sequence:      str = Field(..., min_length=5, max_length=2000)
    variant_sequence: str = Field(..., min_length=5, max_length=2000)


class GrnaRequest(BaseModel):
    target_gene: str = Field(..., min_length=1, max_length=50)
    n_guides:    int = Field(5, ge=1, le=20)


class FluxRequest(BaseModel):
    target_reaction:  Optional[str]       = None
    gene_knockouts:   Optional[List[str]] = None
    overexpressions:  Optional[List[str]] = None


class KnockoutRequest(BaseModel):
    n: int = Field(5, ge=1, le=20)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/llr")
async def get_llr_scores(body: LLRRequest) -> Dict[str, Any]:
    """
    Calculate Log-Likelihood Ratio scores for specific mutations.

    Returns a list of mutations with LLR values and interpretations.
    Positive LLR → model considers the mutant more likely than wild-type.
    """
    try:
        mutations: List[Tuple[int, str, str]] = [
            (m.position, m.wt, m.mt) for m in body.mutations
        ]
        results = _ep().get_llr(body.sequence, mutations)
        return {
            "sequence_length": len(body.sequence),
            "mutations_scored": len(results),
            "results": results,
        }
    except Exception as exc:
        log.error("LLR scoring failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/suggest")
async def suggest_mutations(body: SuggestRequest) -> Dict[str, Any]:
    """
    Suggest the top-k single-point mutations predicted to be beneficial.
    Scans all positions × all amino-acid substitutions.
    """
    try:
        suggestions = _ep().generate_mutations(
            body.sequence, top_k=body.top_k, min_llr=body.min_llr
        )
        return {
            "sequence_length": len(body.sequence),
            "suggestions":     suggestions,
            "count":           len(suggestions),
        }
    except Exception as exc:
        log.error("Mutation suggestion failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/score-variant")
async def score_variant(body: VariantRequest) -> Dict[str, Any]:
    """
    Score a full variant sequence against the wild-type.
    Returns aggregate LLR and per-mutation breakdown.
    """
    try:
        result = _ep().score_variant(body.wt_sequence, body.variant_sequence)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        log.error("Variant scoring failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/grna")
async def design_grna(body: GrnaRequest) -> Dict[str, Any]:
    """
    Design CRISPR gRNA sequences for a target gene.
    Returns ranked guides with on-target and off-target scores.
    """
    try:
        guides = _pd().design_grna(body.target_gene, body.n_guides)
        return {
            "target_gene": body.target_gene,
            "guides":      guides,
            "count":       len(guides),
        }
    except Exception as exc:
        log.error("gRNA design failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/flux")
async def get_flux(body: FluxRequest) -> Dict[str, Any]:
    """
    Run Flux Balance Analysis.
    Optionally set a target reaction and apply gene knockouts / overexpressions.
    """
    try:
        designer = _pd()
        if body.target_reaction:
            designer.set_target(body.target_reaction)
        return designer.get_flux_distribution(
            gene_knockouts=body.gene_knockouts,
            overexpressions=body.overexpressions,
        )
    except Exception as exc:
        log.error("FBA failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/knockouts")
async def find_knockouts(body: KnockoutRequest) -> Dict[str, Any]:
    """
    Identify gene knockout targets predicted to improve target production.
    """
    try:
        targets = _pd().find_knockout_targets(n=body.n)
        return {"targets": targets, "count": len(targets)}
    except Exception as exc:
        log.error("Knockout analysis failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
