"""
Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ReactionInput(BaseModel):
    """Validated input for a discovery run."""
    reaction: str = Field(..., min_length=3, max_length=500,
                          description="Target reaction, e.g. 'ethanol → jet fuel'")
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict)
    user_id: str = Field(default="anonymous", max_length=100)

    @field_validator("reaction")
    @classmethod
    def validate_reaction(cls, v: str) -> str:
        valid_tokens = ["->", "→", "+", "CO2", "H2", "CH3OH", "ethanol",
                        "methanol", "fuel", "jet", "to", "reduction", "oxidation"]
        if not any(tok.lower() in v.lower() for tok in valid_tokens):
            raise ValueError(
                "Reaction must contain valid chemical notation "
                "(e.g. 'CO2 + H2 → CH3OH' or 'ethanol to jet fuel')"
            )
        return v.strip()


class ExperimentInput(BaseModel):
    """Validated input for logging a single experiment."""
    candidate_id: str = Field(..., min_length=1)
    measured_activity: float = Field(..., ge=0, le=1000,
                                     description="Measured activity in mol/g/h")
    measured_selectivity: float = Field(0.0, ge=0, le=1)
    measured_stability: int = Field(0, ge=0, description="Stability in hours")
    temperature: float = Field(350.0, ge=-273.15, le=3000,
                               description="Temperature in °C")
    pressure: float = Field(1.0, ge=0, le=10000, description="Pressure in bar")
    researcher: str = Field("unknown", max_length=100)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class CandidateResult(BaseModel):
    id: str
    name: str
    type: str
    predicted_activity: float
    predicted_selectivity: float
    predicted_stability: int
    uncertainty: float
    score: float
    details: Optional[str] = None
    novelty_score: Optional[float] = None


class DiscoveryResponse(BaseModel):
    run_id: str
    status: str
    total_candidates: int
    known_count: int
    novel_count: int
    candidates: List[CandidateResult]
    created_at: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
