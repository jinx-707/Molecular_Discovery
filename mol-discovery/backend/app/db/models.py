"""
Database models — sync SQLAlchemy (psycopg2).
Covers the full discovery workflow: catalysts, predictions,
experiments, discovery runs, and discrepancies.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Integer, DateTime,
    ForeignKey, JSON, Text, Boolean,
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Catalyst
# ---------------------------------------------------------------------------

class Catalyst(Base):
    __tablename__ = "catalysts"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    composition = Column(JSON, default=dict)        # {"elements": ["Pt","C"], "ratios": [1,4]}
    structure = Column(Text)                        # SMILES or CIF string
    catalyst_type = Column(String(100))             # "heterogeneous" | "homogeneous" | "enzyme"
    reaction_target = Column(String(500))           # e.g. "ethanol → jet fuel"
    conditions = Column(JSON, default=dict)         # {"T": 523, "P": 50}

    # Performance metrics (from literature or experiments)
    reported_activity = Column(Float)
    reported_selectivity = Column(Float)
    reported_stability = Column(Integer)

    source = Column(String(100))                    # "open_catalyst" | "materials_project" | "internal"
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    predictions = relationship("Prediction", back_populates="catalyst", cascade="all, delete-orphan")
    experiments = relationship("Experiment", back_populates="catalyst", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Discovery Run
# ---------------------------------------------------------------------------

class DiscoveryRun(Base):
    __tablename__ = "discovery_runs"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String(255), default="demo_user")
    target_reaction = Column(Text, nullable=False)
    constraints = Column(JSON, default=dict)

    known_count = Column(Integer, default=0)
    novel_count = Column(Integer, default=0)
    status = Column(String(50), default="running")  # running | completed | failed

    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)

    experiments = relationship("Experiment", back_populates="run")


# ---------------------------------------------------------------------------
# Experiment  (measured lab results)
# ---------------------------------------------------------------------------

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(String, primary_key=True, default=_uuid)
    run_id = Column(String, ForeignKey("discovery_runs.id"), nullable=True)
    candidate_id = Column(String, ForeignKey("catalysts.id"), nullable=True)

    # Measured values
    measured_activity = Column(Float)       # mol/g/h
    measured_selectivity = Column(Float)    # 0–1
    measured_stability = Column(Integer)    # hours

    # Conditions used
    temperature = Column(Float)             # °C
    pressure = Column(Float)               # bar
    space_velocity = Column(Float)         # h⁻¹

    # Metadata
    researcher = Column(String(255), default="unknown")
    lab = Column(String(255))
    instrument = Column(String(255))
    protocol_version = Column(String(50))
    replicates = Column(Integer, default=3)

    created_at = Column(DateTime, default=func.now())

    run = relationship("DiscoveryRun", back_populates="experiments")
    catalyst = relationship("Catalyst", back_populates="experiments")
    discrepancies = relationship("Discrepancy", back_populates="experiment", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(String, primary_key=True, default=_uuid)
    candidate_id = Column(String, ForeignKey("catalysts.id"), nullable=True)
    model_version = Column(String(50), default="demo_v1")

    predicted_activity = Column(Float)
    predicted_selectivity = Column(Float)
    predicted_stability = Column(Integer)
    uncertainty = Column(Float)

    created_at = Column(DateTime, default=func.now())

    catalyst = relationship("Catalyst", back_populates="predictions")
    discrepancies = relationship("Discrepancy", back_populates="prediction", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Discrepancy  (prediction vs experiment delta)
# ---------------------------------------------------------------------------

class Discrepancy(Base):
    __tablename__ = "discrepancies"

    id = Column(String, primary_key=True, default=_uuid)
    experiment_id = Column(String, ForeignKey("experiments.id"), nullable=False)
    prediction_id = Column(String, ForeignKey("predictions.id"), nullable=True)

    discrepancy_percent = Column(Float)
    root_cause_hypothesis = Column(Text)
    resolved = Column(Integer, default=0)   # 0 = open, 1 = resolved
    resolved_by = Column(String(255))

    created_at = Column(DateTime, default=func.now())

    experiment = relationship("Experiment", back_populates="discrepancies")
    prediction = relationship("Prediction", back_populates="discrepancies")


# ---------------------------------------------------------------------------
# Energy Profile  (cached DFT/ML reaction energy calculations)
# ---------------------------------------------------------------------------

class EnergyProfile(Base):
    __tablename__ = "energy_profiles"

    id              = Column(String, primary_key=True, default=_uuid)
    catalyst_id     = Column(String, ForeignKey("catalysts.id"), nullable=True)
    reaction_smiles = Column(Text, nullable=False)
    cache_key       = Column(String(16), unique=True, nullable=False, index=True)

    # Computed values
    activation_energy_eV = Column(Float)
    reaction_energy_eV   = Column(Float)
    calculator           = Column(String(50), default="demo")  # "demo"|"ASE-EMT"|"M3GNet"

    # Full profile stored as JSON (NEB images, coordinates, etc.)
    profile_json = Column(Text, nullable=False)

    # Cache management
    cache_expires_at = Column(DateTime, nullable=False)
    created_at       = Column(DateTime, default=func.now())
    updated_at       = Column(DateTime, default=func.now(), onupdate=func.now())


# ---------------------------------------------------------------------------
# Model Metadata  (version history + performance metrics)
# ---------------------------------------------------------------------------

class ModelMetadata(Base):
    __tablename__ = "model_metadata"

    id            = Column(String, primary_key=True, default=_uuid)
    model_version = Column(String(50), nullable=False, unique=True)
    model_type    = Column(String(100), default="CatalystGNN")

    # Training info
    samples_used  = Column(Integer, default=0)
    epochs        = Column(Integer, default=0)
    learning_rate = Column(Float)

    # Validation metrics
    val_mae       = Column(Float)    # Mean Absolute Error on hold-out set
    val_r2        = Column(Float)    # R² on hold-out set
    val_samples   = Column(Integer)

    # Promotion
    is_production = Column(Boolean, default=False)
    promoted_at   = Column(DateTime)
    notes         = Column(Text)

    created_at    = Column(DateTime, default=func.now())


# ---------------------------------------------------------------------------
# Drift Event  (data drift audit log)
# ---------------------------------------------------------------------------

class DriftEvent(Base):
    __tablename__ = "drift_events"

    id               = Column(String, primary_key=True, default=_uuid)
    drift_detected   = Column(Boolean, default=False)
    severity         = Column(String(20), default="none")  # none|low|moderate|high
    max_psi          = Column(Float)
    drifted_features = Column(JSON, default=list)   # ["activity", "temperature"]
    feature_report   = Column(JSON, default=dict)   # full per-feature stats
    summary          = Column(Text)
    trigger          = Column(String(50), default="scheduled")  # scheduled|manual|threshold

    created_at       = Column(DateTime, default=func.now())
