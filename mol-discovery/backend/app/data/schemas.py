import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------

class _TimestampMixin(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserRead(_TimestampMixin):
    id: uuid.UUID
    email: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectRead(_TimestampMixin):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: Optional[str]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Catalyst
# ---------------------------------------------------------------------------

class CatalystCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    smiles: Optional[str] = None
    inchi: Optional[str] = None
    inchi_key: Optional[str] = Field(None, max_length=27)

    composition: Dict[str, float] = Field(default_factory=dict)
    formula: Optional[str] = None
    molecular_weight: Optional[float] = Field(None, gt=0)

    structure_file: Optional[str] = None
    space_group: Optional[str] = None
    crystal_system: Optional[str] = None
    descriptors: Dict[str, Any] = Field(default_factory=dict)

    reaction_type: Optional[str] = None
    reaction_smiles: Optional[str] = None
    target_product: Optional[str] = None

    temperature_k: Optional[float] = Field(None, gt=0)
    pressure_bar: Optional[float] = Field(None, gt=0)
    solvent: Optional[str] = None
    ph: Optional[float] = Field(None, ge=0, le=14)
    conditions: Dict[str, Any] = Field(default_factory=dict)

    source: Optional[str] = None
    external_id: Optional[str] = None
    doi: Optional[str] = None

    @field_validator("composition")
    @classmethod
    def composition_fractions(cls, v: Dict[str, float]) -> Dict[str, float]:
        for element, fraction in v.items():
            if not (0 <= fraction <= 1):
                raise ValueError(f"Fraction for {element} must be between 0 and 1")
        return v


class CatalystRead(_TimestampMixin):
    id: uuid.UUID
    name: str
    smiles: Optional[str]
    inchi_key: Optional[str]
    formula: Optional[str]
    molecular_weight: Optional[float]
    reaction_type: Optional[str]
    source: Optional[str]
    external_id: Optional[str]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Enzyme
# ---------------------------------------------------------------------------

class MutationSchema(BaseModel):
    position: int = Field(..., ge=1)
    from_aa: str = Field(..., alias="from", min_length=1, max_length=3)
    to_aa: str = Field(..., alias="to", min_length=1, max_length=3)

    model_config = {"populate_by_name": True}


class EnzymeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    gene_name: Optional[str] = None
    organism: Optional[str] = None

    amino_acid_sequence: Optional[str] = None
    uniprot_id: Optional[str] = Field(None, max_length=20)
    pdb_id: Optional[str] = Field(None, max_length=10)
    alphafold_id: Optional[str] = None

    ec_number: Optional[str] = Field(None, pattern=r"^\d+\.\d+\.\d+\.\d+$")
    enzyme_class: Optional[str] = None
    cofactors: List[str] = Field(default_factory=list)

    mutations: List[MutationSchema] = Field(default_factory=list)
    is_wildtype: bool = True
    parent_id: Optional[uuid.UUID] = None

    km_mm: Optional[float] = Field(None, gt=0)
    kcat_per_s: Optional[float] = Field(None, gt=0)

    source: Optional[str] = None
    external_id: Optional[str] = None
    doi: Optional[str] = None

    @model_validator(mode="after")
    def set_sequence_length(self) -> "EnzymeCreate":
        if self.amino_acid_sequence:
            object.__setattr__(self, "sequence_length", len(self.amino_acid_sequence))
        return self

    @model_validator(mode="after")
    def variant_requires_parent(self) -> "EnzymeCreate":
        if not self.is_wildtype and self.parent_id is None:
            raise ValueError("Enzyme variants must reference a parent_id")
        return self


class EnzymeRead(_TimestampMixin):
    id: uuid.UUID
    name: str
    organism: Optional[str]
    uniprot_id: Optional[str]
    pdb_id: Optional[str]
    ec_number: Optional[str]
    is_wildtype: bool
    km_mm: Optional[float]
    kcat_per_s: Optional[float]
    source: Optional[str]

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Experiment
# ---------------------------------------------------------------------------

class ExperimentCreate(BaseModel):
    project_id: Optional[uuid.UUID] = None
    catalyst_id: Optional[uuid.UUID] = None
    enzyme_id: Optional[uuid.UUID] = None

    activity: Optional[float] = None
    selectivity: Optional[float] = Field(None, ge=0, le=1)
    stability: Optional[float] = Field(None, ge=0)
    yield_: Optional[float] = Field(None, alias="yield", ge=0, le=1)
    conversion: Optional[float] = Field(None, ge=0, le=1)
    faradaic_efficiency: Optional[float] = Field(None, ge=0, le=1)

    temperature_k: Optional[float] = Field(None, gt=0)
    pressure_bar: Optional[float] = Field(None, gt=0)
    ph: Optional[float] = Field(None, ge=0, le=14)
    solvent: Optional[str] = None
    reaction_time_h: Optional[float] = Field(None, ge=0)
    conditions: Dict[str, Any] = Field(default_factory=dict)

    lab: Optional[str] = None
    operator: Optional[str] = None
    instrument: Optional[str] = None
    batch_id: Optional[str] = None
    raw_data_path: Optional[str] = None
    notes: Optional[str] = None
    measured_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def has_candidate(self) -> "ExperimentCreate":
        if self.catalyst_id is None and self.enzyme_id is None:
            raise ValueError("Experiment must reference either a catalyst_id or enzyme_id")
        return self


class ExperimentRead(_TimestampMixin):
    id: uuid.UUID
    catalyst_id: Optional[uuid.UUID]
    enzyme_id: Optional[uuid.UUID]
    activity: Optional[float]
    selectivity: Optional[float]
    stability: Optional[float]
    measured_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

class PredictionCreate(BaseModel):
    run_id: str = Field(..., min_length=1)
    model_name: str = Field(..., min_length=1)
    model_version: Optional[str] = None

    catalyst_id: Optional[uuid.UUID] = None
    enzyme_id: Optional[uuid.UUID] = None

    predicted_activity: Optional[float] = None
    predicted_selectivity: Optional[float] = Field(None, ge=0, le=1)
    predicted_stability: Optional[float] = Field(None, ge=0)
    predicted_yield: Optional[float] = Field(None, ge=0, le=1)

    uncertainty_activity: Optional[float] = Field(None, ge=0)
    uncertainty_selectivity: Optional[float] = Field(None, ge=0)
    uncertainty_stability: Optional[float] = Field(None, ge=0)

    raw_output: Dict[str, Any] = Field(default_factory=dict)


class PredictionRead(BaseModel):
    id: uuid.UUID
    run_id: str
    model_name: str
    catalyst_id: Optional[uuid.UUID]
    enzyme_id: Optional[uuid.UUID]
    predicted_activity: Optional[float]
    predicted_selectivity: Optional[float]
    predicted_stability: Optional[float]
    uncertainty_activity: Optional[float]
    predicted_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Discrepancy
# ---------------------------------------------------------------------------

class DiscrepancyCreate(BaseModel):
    experiment_id: uuid.UUID
    prediction_id: uuid.UUID

    delta_activity: Optional[float] = None
    delta_selectivity: Optional[float] = None
    delta_stability: Optional[float] = None
    relative_error_activity: Optional[float] = None
    relative_error_selectivity: Optional[float] = None

    severity: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    root_cause_hypothesis: Optional[str] = None
    auto_flags: List[str] = Field(default_factory=list)


class DiscrepancyRead(BaseModel):
    id: uuid.UUID
    experiment_id: uuid.UUID
    prediction_id: uuid.UUID
    delta_activity: Optional[float]
    delta_selectivity: Optional[float]
    severity: Optional[str]
    root_cause_hypothesis: Optional[str]
    reviewed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Annotation
# ---------------------------------------------------------------------------

class AnnotationCreate(BaseModel):
    catalyst_id: Optional[uuid.UUID] = None
    enzyme_id: Optional[uuid.UUID] = None
    label: str = Field(..., min_length=1, max_length=100)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    comment: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def has_target(self) -> "AnnotationCreate":
        if self.catalyst_id is None and self.enzyme_id is None:
            raise ValueError("Annotation must target either a catalyst_id or enzyme_id")
        return self


class AnnotationRead(_TimestampMixin):
    id: uuid.UUID
    user_id: uuid.UUID
    catalyst_id: Optional[uuid.UUID]
    enzyme_id: Optional[uuid.UUID]
    label: str
    confidence: Optional[float]
    tags: List[str]

    model_config = {"from_attributes": True}
