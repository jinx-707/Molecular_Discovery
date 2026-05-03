import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float, ForeignKey,
    Index, Integer, JSON, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.utcnow()


# ---------------------------------------------------------------------------
# User / Project
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    annotations = relationship("Annotation", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="projects")
    experiments = relationship("Experiment", back_populates="project")

    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_project_owner_name"),
    )


# ---------------------------------------------------------------------------
# Catalyst
# ---------------------------------------------------------------------------

class Catalyst(Base):
    __tablename__ = "catalysts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    smiles = Column(Text)
    inchi = Column(Text)
    inchi_key = Column(String(27), unique=True, index=True)

    # Composition
    composition = Column(JSON, default=dict)          # {"Fe": 0.5, "Ni": 0.5}
    formula = Column(String(255))
    molecular_weight = Column(Float)

    # Structure descriptors
    structure_file = Column(Text)                     # CIF / XYZ content
    space_group = Column(String(50))
    crystal_system = Column(String(50))
    descriptors = Column(JSON, default=dict)          # Morgan FP, RDKit descriptors, etc.

    # Reaction context
    reaction_type = Column(String(255))               # e.g. "CO2 reduction"
    reaction_smiles = Column(Text)
    target_product = Column(String(255))

    # Operating conditions
    temperature_k = Column(Float)
    pressure_bar = Column(Float)
    solvent = Column(String(255))
    ph = Column(Float)
    conditions = Column(JSON, default=dict)           # catch-all for extra fields

    # Provenance
    source = Column(String(100))                      # "OC20", "materials_project", "internal"
    external_id = Column(String(255))
    doi = Column(String(255))

    # Vector embedding (stored as float array; also mirrored in Qdrant)
    embedding = Column(ARRAY(Float))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    experiments = relationship("Experiment", back_populates="catalyst")
    predictions = relationship("Prediction", back_populates="catalyst")
    annotations = relationship("Annotation", back_populates="catalyst")

    __table_args__ = (
        Index("ix_catalysts_source_external", "source", "external_id"),
        Index("ix_catalysts_reaction_type", "reaction_type"),
    )


# ---------------------------------------------------------------------------
# Enzyme
# ---------------------------------------------------------------------------

class Enzyme(Base):
    __tablename__ = "enzymes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    gene_name = Column(String(255))
    organism = Column(String(255))

    # Sequence
    amino_acid_sequence = Column(Text)
    sequence_length = Column(Integer)
    uniprot_id = Column(String(20), unique=True, index=True)

    # Structure
    pdb_id = Column(String(10), index=True)
    alphafold_id = Column(String(50))
    structure_file = Column(Text)                     # PDB content

    # Classification
    ec_number = Column(String(20), index=True)        # e.g. "1.1.1.1"
    enzyme_class = Column(String(100))
    cofactors = Column(ARRAY(String))

    # Mutations
    mutations = Column(JSON, default=list)            # [{"position": 42, "from": "A", "to": "G"}]
    is_wildtype = Column(Boolean, default=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("enzymes.id"), nullable=True)

    # Kinetics (reference values)
    km_mm = Column(Float)                             # Michaelis constant mM
    kcat_per_s = Column(Float)                        # turnover number s⁻¹
    kcat_km = Column(Float)                           # catalytic efficiency

    # Provenance
    source = Column(String(100))                      # "brenda", "uniprot", "internal"
    external_id = Column(String(255))
    doi = Column(String(255))

    embedding = Column(ARRAY(Float))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    variants = relationship("Enzyme", backref="parent", foreign_keys=[parent_id])
    experiments = relationship("Experiment", back_populates="enzyme")
    predictions = relationship("Prediction", back_populates="enzyme")
    annotations = relationship("Annotation", back_populates="enzyme")

    __table_args__ = (
        Index("ix_enzymes_ec_organism", "ec_number", "organism"),
    )


# ---------------------------------------------------------------------------
# Experiment  (time-series table → TimescaleDB hypertable on measured_at)
# ---------------------------------------------------------------------------

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)

    # Candidate — exactly one of these is set
    catalyst_id = Column(UUID(as_uuid=True), ForeignKey("catalysts.id", ondelete="SET NULL"), nullable=True)
    enzyme_id = Column(UUID(as_uuid=True), ForeignKey("enzymes.id", ondelete="SET NULL"), nullable=True)

    # Measured performance
    activity = Column(Float)                          # e.g. TOF h⁻¹ or µmol/min/mg
    selectivity = Column(Float)                       # 0–1
    stability = Column(Float)                         # half-life hours
    yield_ = Column("yield", Float)
    conversion = Column(Float)
    faradaic_efficiency = Column(Float)

    # Conditions at measurement time
    temperature_k = Column(Float)
    pressure_bar = Column(Float)
    ph = Column(Float)
    solvent = Column(String(255))
    reaction_time_h = Column(Float)
    conditions = Column(JSON, default=dict)

    # Provenance
    lab = Column(String(255))
    operator = Column(String(255))
    instrument = Column(String(255))
    batch_id = Column(String(255))
    raw_data_path = Column(Text)
    notes = Column(Text)

    measured_at = Column(DateTime(timezone=True), nullable=False, default=_now, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    project = relationship("Project", back_populates="experiments")
    catalyst = relationship("Catalyst", back_populates="experiments")
    enzyme = relationship("Enzyme", back_populates="experiments")
    discrepancies = relationship("Discrepancy", back_populates="experiment", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_experiments_measured_at", "measured_at"),
        Index("ix_experiments_catalyst_id", "catalyst_id"),
        Index("ix_experiments_enzyme_id", "enzyme_id"),
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(String(255), nullable=False, index=True)   # ML pipeline run identifier
    model_name = Column(String(255), nullable=False)
    model_version = Column(String(50))

    catalyst_id = Column(UUID(as_uuid=True), ForeignKey("catalysts.id", ondelete="SET NULL"), nullable=True)
    enzyme_id = Column(UUID(as_uuid=True), ForeignKey("enzymes.id", ondelete="SET NULL"), nullable=True)

    # Predicted values
    predicted_activity = Column(Float)
    predicted_selectivity = Column(Float)
    predicted_stability = Column(Float)
    predicted_yield = Column(Float)

    # Uncertainty (std dev or confidence interval half-width)
    uncertainty_activity = Column(Float)
    uncertainty_selectivity = Column(Float)
    uncertainty_stability = Column(Float)

    # Full distribution / extra outputs
    raw_output = Column(JSON, default=dict)

    predicted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    catalyst = relationship("Catalyst", back_populates="predictions")
    enzyme = relationship("Enzyme", back_populates="predictions")
    discrepancies = relationship("Discrepancy", back_populates="prediction", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_predictions_run_id", "run_id"),
        Index("ix_predictions_catalyst_id", "catalyst_id"),
    )


# ---------------------------------------------------------------------------
# Discrepancy
# ---------------------------------------------------------------------------

class Discrepancy(Base):
    __tablename__ = "discrepancies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False)

    # Delta (predicted − actual)
    delta_activity = Column(Float)
    delta_selectivity = Column(Float)
    delta_stability = Column(Float)

    # Relative error
    relative_error_activity = Column(Float)
    relative_error_selectivity = Column(Float)

    # Analysis
    severity = Column(String(20))                     # "low" | "medium" | "high"
    root_cause_hypothesis = Column(Text)
    auto_flags = Column(JSON, default=list)           # ["outlier", "data_quality", ...]
    reviewed = Column(Boolean, default=False)
    reviewer_notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    experiment = relationship("Experiment", back_populates="discrepancies")
    prediction = relationship("Prediction", back_populates="discrepancies")

    __table_args__ = (
        UniqueConstraint("experiment_id", "prediction_id", name="uq_discrepancy_exp_pred"),
        Index("ix_discrepancies_severity", "severity"),
    )


# ---------------------------------------------------------------------------
# Annotation
# ---------------------------------------------------------------------------

class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    catalyst_id = Column(UUID(as_uuid=True), ForeignKey("catalysts.id", ondelete="CASCADE"), nullable=True)
    enzyme_id = Column(UUID(as_uuid=True), ForeignKey("enzymes.id", ondelete="CASCADE"), nullable=True)

    label = Column(String(100), nullable=False)       # e.g. "promising", "discard", "retest"
    confidence = Column(Float)                        # 0–1
    comment = Column(Text)
    tags = Column(ARRAY(String), default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="annotations")
    catalyst = relationship("Catalyst", back_populates="annotations")
    enzyme = relationship("Enzyme", back_populates="annotations")

    __table_args__ = (
        Index("ix_annotations_label", "label"),
        Index("ix_annotations_user_id", "user_id"),
    )
