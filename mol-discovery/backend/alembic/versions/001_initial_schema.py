"""Initial schema – all tables, indexes, TimescaleDB hypertable

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ------------------------------------------------------------------
    # projects
    # ------------------------------------------------------------------
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("metadata", sa.JSON(), server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("owner_id", "name", name="uq_project_owner_name"),
    )

    # ------------------------------------------------------------------
    # catalysts
    # ------------------------------------------------------------------
    op.create_table(
        "catalysts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("smiles", sa.Text()),
        sa.Column("inchi", sa.Text()),
        sa.Column("inchi_key", sa.String(27)),
        sa.Column("composition", sa.JSON(), server_default="{}"),
        sa.Column("formula", sa.String(255)),
        sa.Column("molecular_weight", sa.Float()),
        sa.Column("structure_file", sa.Text()),
        sa.Column("space_group", sa.String(50)),
        sa.Column("crystal_system", sa.String(50)),
        sa.Column("descriptors", sa.JSON(), server_default="{}"),
        sa.Column("reaction_type", sa.String(255)),
        sa.Column("reaction_smiles", sa.Text()),
        sa.Column("target_product", sa.String(255)),
        sa.Column("temperature_k", sa.Float()),
        sa.Column("pressure_bar", sa.Float()),
        sa.Column("solvent", sa.String(255)),
        sa.Column("ph", sa.Float()),
        sa.Column("conditions", sa.JSON(), server_default="{}"),
        sa.Column("source", sa.String(100)),
        sa.Column("external_id", sa.String(255)),
        sa.Column("doi", sa.String(255)),
        sa.Column("embedding", postgresql.ARRAY(sa.Float())),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_catalysts_inchi_key", "catalysts", ["inchi_key"], unique=True)
    op.create_index("ix_catalysts_source_external", "catalysts", ["source", "external_id"])
    op.create_index("ix_catalysts_reaction_type", "catalysts", ["reaction_type"])

    # ------------------------------------------------------------------
    # enzymes
    # ------------------------------------------------------------------
    op.create_table(
        "enzymes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("gene_name", sa.String(255)),
        sa.Column("organism", sa.String(255)),
        sa.Column("amino_acid_sequence", sa.Text()),
        sa.Column("sequence_length", sa.Integer()),
        sa.Column("uniprot_id", sa.String(20)),
        sa.Column("pdb_id", sa.String(10)),
        sa.Column("alphafold_id", sa.String(50)),
        sa.Column("structure_file", sa.Text()),
        sa.Column("ec_number", sa.String(20)),
        sa.Column("enzyme_class", sa.String(100)),
        sa.Column("cofactors", postgresql.ARRAY(sa.String())),
        sa.Column("mutations", sa.JSON(), server_default="[]"),
        sa.Column("is_wildtype", sa.Boolean(), server_default="true"),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("enzymes.id"), nullable=True),
        sa.Column("km_mm", sa.Float()),
        sa.Column("kcat_per_s", sa.Float()),
        sa.Column("kcat_km", sa.Float()),
        sa.Column("source", sa.String(100)),
        sa.Column("external_id", sa.String(255)),
        sa.Column("doi", sa.String(255)),
        sa.Column("embedding", postgresql.ARRAY(sa.Float())),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_enzymes_uniprot_id", "enzymes", ["uniprot_id"], unique=True)
    op.create_index("ix_enzymes_pdb_id", "enzymes", ["pdb_id"])
    op.create_index("ix_enzymes_ec_number", "enzymes", ["ec_number"])
    op.create_index("ix_enzymes_ec_organism", "enzymes", ["ec_number", "organism"])

    # ------------------------------------------------------------------
    # experiments  (will become TimescaleDB hypertable)
    # ------------------------------------------------------------------
    op.create_table(
        "experiments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("catalyst_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("catalysts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("enzyme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("enzymes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("activity", sa.Float()),
        sa.Column("selectivity", sa.Float()),
        sa.Column("stability", sa.Float()),
        sa.Column("yield", sa.Float()),
        sa.Column("conversion", sa.Float()),
        sa.Column("faradaic_efficiency", sa.Float()),
        sa.Column("temperature_k", sa.Float()),
        sa.Column("pressure_bar", sa.Float()),
        sa.Column("ph", sa.Float()),
        sa.Column("solvent", sa.String(255)),
        sa.Column("reaction_time_h", sa.Float()),
        sa.Column("conditions", sa.JSON(), server_default="{}"),
        sa.Column("lab", sa.String(255)),
        sa.Column("operator", sa.String(255)),
        sa.Column("instrument", sa.String(255)),
        sa.Column("batch_id", sa.String(255)),
        sa.Column("raw_data_path", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_experiments_measured_at", "experiments", ["measured_at"])
    op.create_index("ix_experiments_catalyst_id", "experiments", ["catalyst_id"])
    op.create_index("ix_experiments_enzyme_id", "experiments", ["enzyme_id"])

    # Convert experiments to TimescaleDB hypertable partitioned by measured_at
    op.execute(
        "SELECT create_hypertable('experiments', 'measured_at', "
        "if_not_exists => TRUE, migrate_data => TRUE);"
    )

    # ------------------------------------------------------------------
    # predictions
    # ------------------------------------------------------------------
    op.create_table(
        "predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", sa.String(255), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("model_version", sa.String(50)),
        sa.Column("catalyst_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("catalysts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("enzyme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("enzymes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("predicted_activity", sa.Float()),
        sa.Column("predicted_selectivity", sa.Float()),
        sa.Column("predicted_stability", sa.Float()),
        sa.Column("predicted_yield", sa.Float()),
        sa.Column("uncertainty_activity", sa.Float()),
        sa.Column("uncertainty_selectivity", sa.Float()),
        sa.Column("uncertainty_stability", sa.Float()),
        sa.Column("raw_output", sa.JSON(), server_default="{}"),
        sa.Column("predicted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_predictions_run_id", "predictions", ["run_id"])
    op.create_index("ix_predictions_catalyst_id", "predictions", ["catalyst_id"])

    # ------------------------------------------------------------------
    # discrepancies
    # ------------------------------------------------------------------
    op.create_table(
        "discrepancies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("delta_activity", sa.Float()),
        sa.Column("delta_selectivity", sa.Float()),
        sa.Column("delta_stability", sa.Float()),
        sa.Column("relative_error_activity", sa.Float()),
        sa.Column("relative_error_selectivity", sa.Float()),
        sa.Column("severity", sa.String(20)),
        sa.Column("root_cause_hypothesis", sa.Text()),
        sa.Column("auto_flags", sa.JSON(), server_default="[]"),
        sa.Column("reviewed", sa.Boolean(), server_default="false"),
        sa.Column("reviewer_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("experiment_id", "prediction_id", name="uq_discrepancy_exp_pred"),
    )
    op.create_index("ix_discrepancies_severity", "discrepancies", ["severity"])

    # ------------------------------------------------------------------
    # annotations
    # ------------------------------------------------------------------
    op.create_table(
        "annotations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("catalyst_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("catalysts.id", ondelete="CASCADE"), nullable=True),
        sa.Column("enzyme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("enzymes.id", ondelete="CASCADE"), nullable=True),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("comment", sa.Text()),
        sa.Column("tags", postgresql.ARRAY(sa.String())),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_annotations_label", "annotations", ["label"])
    op.create_index("ix_annotations_user_id", "annotations", ["user_id"])


def downgrade() -> None:
    op.drop_table("annotations")
    op.drop_table("discrepancies")
    op.drop_table("predictions")
    op.drop_table("experiments")
    op.drop_table("enzymes")
    op.drop_table("catalysts")
    op.drop_table("projects")
    op.drop_table("users")
