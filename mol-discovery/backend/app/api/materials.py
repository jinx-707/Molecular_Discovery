"""
Materials & Catalyst Data API
==============================
GET  /api/materials/ocp/search          — OCP catalyst search by reaction
GET  /api/materials/ocp/adsorption      — OCP adsorption energies for a surface
GET  /api/materials/mp/search           — Materials Project search
GET  /api/materials/mp/{material_id}    — Single MP material detail
POST /api/materials/import              — Import MP/OCP/BRENDA results into the DB
GET  /api/materials/brenda/search       — BRENDA enzyme kinetics search
GET  /api/materials/brenda/kcat-km      — kcat/Km values from BRENDA
GET  /api/materials/brenda/km           — Km values from BRENDA
GET  /api/materials/brenda/kcat         — kcat values from BRENDA
GET  /api/materials/status              — Connection status for all sources
"""
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.data.external_sources import (
    MaterialsProjectClient,
    MaterialsProjectService,
    OpenCatalystClient,
    BrendaClient,
)
from app.db.session import SessionLocal
from app.db.models import Catalyst

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/materials", tags=["materials"])

# Lazy singletons
_ocp:    Optional[OpenCatalystClient]       = None
_mp:     Optional[MaterialsProjectClient]   = None
_mps:    Optional[MaterialsProjectService]  = None
_brenda: Optional[BrendaClient]             = None


def _get_ocp() -> OpenCatalystClient:
    global _ocp
    if _ocp is None:
        _ocp = OpenCatalystClient()
    return _ocp


def _get_mp() -> MaterialsProjectClient:
    global _mp
    if _mp is None:
        _mp = MaterialsProjectClient()
    return _mp


def _get_mps() -> MaterialsProjectService:
    global _mps
    if _mps is None:
        _mps = MaterialsProjectService()
    return _mps


def _get_brenda() -> BrendaClient:
    global _brenda
    if _brenda is None:
        _brenda = BrendaClient()
    return _brenda


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ImportRequest(BaseModel):
    source:      str                    # "ocp" | "mp" | "brenda"
    reaction:    Optional[str] = None   # for OCP
    elements:    Optional[List[str]] = None  # for MP
    formula:     Optional[str] = None   # for MP
    ec_number:   Optional[str] = None   # for BRENDA
    organism:    Optional[str] = None   # for BRENDA
    substrate:   Optional[str] = None   # for BRENDA
    limit:       int = 20
    reaction_target: str = ""           # stored on the Catalyst row


# ---------------------------------------------------------------------------
# OCP endpoints
# ---------------------------------------------------------------------------

@router.get("/ocp/search")
async def ocp_search(
    reaction: str = Query(..., description="Reaction type, e.g. 'CO2 reduction'"),
    limit:    int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """Search OCP for catalysts relevant to a reaction type."""
    try:
        results = _get_ocp().search_catalysts(reaction, limit=limit)
        return {
            "source":  "open_catalyst",
            "demo":    _get_ocp().demo_mode,
            "count":   len(results),
            "results": results,
        }
    except Exception as exc:
        log.error("OCP search failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ocp/adsorption")
async def ocp_adsorption(
    formula:   str = Query(..., description="Bulk formula, e.g. 'Cu', 'Pt3Ni'"),
    adsorbate: str = Query("*CO", description="Adsorbate, e.g. '*CO', '*H', '*OH'"),
    limit:     int = Query(10, ge=1, le=50),
) -> Dict[str, Any]:
    """Get adsorption energies for a surface + adsorbate pair from OCP."""
    try:
        results = _get_ocp().get_adsorption_energies_sync(formula, adsorbate, limit)
        return {
            "source":    "open_catalyst",
            "formula":   formula,
            "adsorbate": adsorbate,
            "demo":      _get_ocp().demo_mode,
            "count":     len(results),
            "results":   results,
        }
    except Exception as exc:
        log.error("OCP adsorption failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Materials Project endpoints
# ---------------------------------------------------------------------------

@router.get("/mp/search")
async def mp_search(
    elements:     Optional[str] = Query(None, description="Comma-separated elements, e.g. 'Cu,Zn'"),
    formula:      Optional[str] = Query(None, description="Exact formula, e.g. 'Cu2O'"),
    max_band_gap: Optional[float] = Query(None, description="Max band gap in eV"),
    limit:        int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """Search the Materials Project for catalyst materials."""
    try:
        el_list = [e.strip() for e in elements.split(",")] if elements else None
        results = _get_mp().search_catalysts(
            elements=el_list,
            formula=formula,
            max_band_gap=max_band_gap,
            limit=limit,
        )
        return {
            "source":  "materials_project",
            "demo":    _get_mp().demo_mode,
            "count":   len(results),
            "results": results,
        }
    except Exception as exc:
        log.error("MP search failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/mp/{material_id}")
async def mp_get_material(material_id: str) -> Dict[str, Any]:
    """Fetch a single material by its Materials Project ID (e.g. mp-30)."""
    try:
        result = _get_mp().get_material(material_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Material {material_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as exc:
        log.error("MP get_material failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/mp/elements/{elements}")
async def mp_search_by_elements(
    elements: str,
    limit:    int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """
    Search MP for materials containing specific elements.
    elements: comma-separated, e.g. 'Cu,Zn' or 'Fe,Ni,Co'
    """
    try:
        el_list = [e.strip() for e in elements.split(",") if e.strip()]
        results = _get_mps().search_catalysts_by_elements(el_list, limit=limit)
        return {
            "source":   "materials_project",
            "demo":     _get_mps().demo_mode,
            "elements": el_list,
            "count":    len(results),
            "results":  results,
        }
    except Exception as exc:
        log.error("MP elements search failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/mp/stable")
async def mp_search_stable(
    elements:     Optional[str]   = Query(None, description="Comma-separated elements"),
    max_band_gap: Optional[float] = Query(None, description="Max band gap in eV"),
    limit:        int             = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """Return only thermodynamically stable materials (energy_above_hull = 0)."""
    try:
        el_list = [e.strip() for e in elements.split(",")] if elements else None
        results = _get_mps().search_stable_catalysts(
            elements=el_list, max_band_gap=max_band_gap, limit=limit
        )
        return {
            "source":  "materials_project",
            "demo":    _get_mps().demo_mode,
            "filter":  "stable (e_hull=0)",
            "count":   len(results),
            "results": results,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/mp/metals")
async def mp_search_metals(
    elements: Optional[str] = Query(None),
    limit:    int           = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """Return metallic materials (band_gap ≈ 0) — good for hydrogenation."""
    try:
        el_list = [e.strip() for e in elements.split(",")] if elements else None
        results = _get_mps().search_metals(elements=el_list, limit=limit)
        return {
            "source":  "materials_project",
            "demo":    _get_mps().demo_mode,
            "filter":  "metals (band_gap=0)",
            "count":   len(results),
            "results": results,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# BRENDA endpoints
# ---------------------------------------------------------------------------

@router.get("/brenda/search")
async def brenda_search(
    ec_number: str = Query("*", description="EC number, e.g. '1.1.1.1' or '*' for all"),
    organism:  str = Query("*", description="Organism, e.g. 'Homo sapiens' or '*'"),
    substrate: str = Query("*", description="Substrate, e.g. 'ethanol' or '*'"),
    limit:     int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """Search BRENDA for enzyme kinetic data (kcat/Km, Km, kcat)."""
    try:
        results = _get_brenda().search_enzymes(ec_number, organism, substrate, limit)
        return {
            "source":    "brenda",
            "demo":      _get_brenda().demo_mode,
            "count":     len(results),
            "results":   results,
        }
    except Exception as exc:
        log.error("BRENDA search failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/brenda/kcat-km")
async def brenda_kcat_km(
    ec_number: str = Query("*"),
    organism:  str = Query("*"),
    substrate: str = Query("*"),
    limit:     int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """Fetch kcat/Km (catalytic efficiency) values from BRENDA."""
    try:
        results = _get_brenda().get_kcat_km(ec_number, organism, substrate, limit)
        return {
            "source":  "brenda",
            "demo":    _get_brenda().demo_mode,
            "metric":  "kcat_km",
            "unit":    "mM⁻¹s⁻¹",
            "count":   len(results),
            "results": results,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/brenda/km")
async def brenda_km(
    ec_number: str = Query("*"),
    organism:  str = Query("*"),
    substrate: str = Query("*"),
    limit:     int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """Fetch Km (Michaelis constant) values in mM from BRENDA."""
    try:
        results = _get_brenda().get_km(ec_number, organism, substrate, limit)
        return {
            "source":  "brenda",
            "demo":    _get_brenda().demo_mode,
            "metric":  "km",
            "unit":    "mM",
            "count":   len(results),
            "results": results,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/brenda/kcat")
async def brenda_kcat(
    ec_number: str = Query("*"),
    organism:  str = Query("*"),
    substrate: str = Query("*"),
    limit:     int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """Fetch kcat (turnover number) values in s⁻¹ from BRENDA."""
    try:
        results = _get_brenda().get_kcat(ec_number, organism, substrate, limit)
        return {
            "source":  "brenda",
            "demo":    _get_brenda().demo_mode,
            "metric":  "kcat",
            "unit":    "s⁻¹",
            "count":   len(results),
            "results": results,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Import endpoint — saves external results into the local DB
# ---------------------------------------------------------------------------

@router.post("/import")
async def import_materials(body: ImportRequest) -> Dict[str, Any]:
    """
    Fetch materials from OCP or MP and persist them as Catalyst rows.
    Skips duplicates (matched by name).
    """
    db = SessionLocal()
    imported = 0
    skipped  = 0

    try:
        records: List[Dict] = []

        if body.source == "ocp":
            raw = _get_ocp().search_catalysts(
                body.reaction or "CO2 reduction", limit=body.limit
            )
            records = [_get_ocp()._enrich(r) for r in raw]

        elif body.source == "mp":
            raw = _get_mps().search_catalysts_by_elements(
                elements=body.elements or [],
                limit=body.limit,
            ) if body.elements else _get_mp().search_catalysts(
                formula=body.formula,
                limit=body.limit,
            )
            records = [_get_mp().to_catalyst_dict(r) for r in raw]

        elif body.source == "brenda":
            raw = _get_brenda().search_enzymes(
                ec_number=body.ec_number or "*",
                organism=body.organism  or "*",
                substrate=body.substrate or "*",
                limit=body.limit,
            )
            records = [_get_brenda().to_enzyme_dict(r) for r in raw]

        else:
            raise HTTPException(
                status_code=400,
                detail="source must be 'ocp', 'mp', or 'brenda'",
            )

        for rec in records:
            name = rec.get("name") or rec.get("formula", "Unknown")
            # Skip if already in DB
            exists = db.query(Catalyst).filter(Catalyst.name == name).first()
            if exists:
                skipped += 1
                continue

            cat = Catalyst(
                id=str(uuid.uuid4()),
                name=name,
                composition=rec.get("composition", {"formula": rec.get("formula", "")}),
                catalyst_type=rec.get("catalyst_type", "heterogeneous"),
                reaction_target=body.reaction_target or rec.get("reaction_type", ""),
                reported_activity=rec.get("activity"),
                reported_selectivity=rec.get("selectivity"),
                reported_stability=rec.get("stability"),
                source=rec.get("source", body.source),
            )
            db.add(cat)
            imported += 1

        db.commit()

        return {
            "status":   "success",
            "imported": imported,
            "skipped":  skipped,
            "total":    len(records),
            "source":   body.source,
        }

    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        log.error("Import failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Status endpoint
# ---------------------------------------------------------------------------

@router.get("/status")
async def materials_status() -> Dict[str, Any]:
    """Check connectivity status for OCP, Materials Project, and BRENDA."""
    ocp    = _get_ocp()
    mp     = _get_mp()
    brenda = _get_brenda()

    return {
        "open_catalyst": {
            "available": not ocp.demo_mode,
            "mode":      "live" if not ocp.demo_mode else "demo",
            "install":   "pip install fairchem-demo-ocpapi",
        },
        "materials_project": {
            "available": not mp.demo_mode,
            "mode":      "live" if not mp.demo_mode else "demo",
            "key_set":   bool(mp._api_key),
            "install":   "pip install mp-api",
        },
        "brenda": {
            "available":    not brenda.demo_mode,
            "mode":         "live" if not brenda.demo_mode else "demo",
            "credentials":  bool(brenda._email and brenda._password),
            "install":      "pip install zeep",
            "wsdl":         "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl",
        },
    }
