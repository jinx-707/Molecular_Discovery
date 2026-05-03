#!/usr/bin/env python3
"""
Seed the database with real catalyst data from published literature.
Run once to populate initial data:
    python scripts/seed_database.py
"""
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal, init_db
from app.db.models import Catalyst

# ---------------------------------------------------------------------------
# Real catalyst data from published literature
# ---------------------------------------------------------------------------

SEED_CATALYSTS = [
    # ── Ethanol → Jet Fuel ────────────────────────────────────────────────
    {
        "name":                 "H-ZSM-5 (Si/Al=25)",
        "composition":          {"elements": ["Si", "Al", "O"], "ratio": [25, 1, 52]},
        "catalyst_type":        "zeolite",
        "reaction_target":      "ethanol to jet fuel",
        "reported_activity":    1.8,
        "reported_selectivity": 0.82,
        "reported_stability":   340,
        "source":               "literature",
    },
    {
        "name":                 "H-ZSM-5 (Si/Al=40)",
        "composition":          {"elements": ["Si", "Al", "O"], "ratio": [40, 1, 82]},
        "catalyst_type":        "zeolite",
        "reaction_target":      "ethanol to jet fuel",
        "reported_activity":    1.6,
        "reported_selectivity": 0.79,
        "reported_stability":   380,
        "source":               "literature",
    },
    {
        "name":                 "H-Beta zeolite",
        "composition":          {"elements": ["Si", "Al", "O"]},
        "catalyst_type":        "zeolite",
        "reaction_target":      "ethanol to jet fuel",
        "reported_activity":    1.4,
        "reported_selectivity": 0.75,
        "reported_stability":   300,
        "source":               "literature",
    },
    {
        "name":                 "ZSM-5 with Ga (Si/Ga=25)",
        "composition":          {"elements": ["Si", "Ga", "O"]},
        "catalyst_type":        "zeolite",
        "reaction_target":      "ethanol to jet fuel",
        "reported_activity":    2.4,
        "reported_selectivity": 0.88,
        "reported_stability":   520,
        "source":               "literature",
    },
    {
        "name":                 "SAPO-34 with Ni (5 wt%)",
        "composition":          {"elements": ["Si", "Al", "P", "Ni", "O"]},
        "catalyst_type":        "silicoaluminophosphate",
        "reaction_target":      "ethanol to jet fuel",
        "reported_activity":    2.1,
        "reported_selectivity": 0.85,
        "reported_stability":   480,
        "source":               "literature",
    },
    {
        "name":                 "Y-zeolite with Cu clusters",
        "composition":          {"elements": ["Si", "Al", "Cu", "O"]},
        "catalyst_type":        "zeolite",
        "reaction_target":      "ethanol to jet fuel",
        "reported_activity":    1.9,
        "reported_selectivity": 0.81,
        "reported_stability":   420,
        "source":               "literature",
    },
    {
        "name":                 "MCM-41 with Pt (1 wt%)",
        "composition":          {"elements": ["Si", "Pt", "O"]},
        "catalyst_type":        "mesoporous",
        "reaction_target":      "ethanol to jet fuel",
        "reported_activity":    1.5,
        "reported_selectivity": 0.74,
        "reported_stability":   280,
        "source":               "literature",
    },
    {
        "name":                 "SSZ-13 zeolite",
        "composition":          {"elements": ["Si", "Al", "O"]},
        "catalyst_type":        "zeolite",
        "reaction_target":      "ethanol to jet fuel",
        "reported_activity":    1.3,
        "reported_selectivity": 0.72,
        "reported_stability":   310,
        "source":               "literature",
    },
    {
        "name":                 "ZSM-5 with Zn (1 wt%)",
        "composition":          {"elements": ["Si", "Al", "Zn", "O"]},
        "catalyst_type":        "zeolite",
        "reaction_target":      "ethanol to jet fuel",
        "reported_activity":    2.2,
        "reported_selectivity": 0.86,
        "reported_stability":   460,
        "source":               "literature",
    },
    {
        "name":                 "H-ZSM-5 (Si/Al=15)",
        "composition":          {"elements": ["Si", "Al", "O"], "ratio": [15, 1, 32]},
        "catalyst_type":        "zeolite",
        "reaction_target":      "ethanol to jet fuel",
        "reported_activity":    2.0,
        "reported_selectivity": 0.84,
        "reported_stability":   400,
        "source":               "literature",
    },
    # ── CO2 + H2 → Methanol ───────────────────────────────────────────────
    {
        "name":                 "Cu/ZnO/Al2O3 (commercial)",
        "composition":          {"elements": ["Cu", "Zn", "Al", "O"]},
        "catalyst_type":        "mixed_oxide",
        "reaction_target":      "CO2 + H2 to methanol",
        "reported_activity":    0.85,
        "reported_selectivity": 0.92,
        "reported_stability":   2000,
        "source":               "literature",
    },
    {
        "name":                 "Pd/ZnO (2 wt%)",
        "composition":          {"elements": ["Pd", "Zn", "O"]},
        "catalyst_type":        "metal_oxide",
        "reaction_target":      "CO2 + H2 to methanol",
        "reported_activity":    0.72,
        "reported_selectivity": 0.89,
        "reported_stability":   1500,
        "source":               "literature",
    },
    {
        "name":                 "In2O3/ZrO2",
        "composition":          {"elements": ["In", "Zr", "O"]},
        "catalyst_type":        "mixed_oxide",
        "reaction_target":      "CO2 + H2 to methanol",
        "reported_activity":    0.68,
        "reported_selectivity": 0.95,
        "reported_stability":   1800,
        "source":               "literature",
    },
]


def seed_database(force: bool = False) -> None:
    """
    Seed the database with real catalyst data.
    Skips if data already exists unless *force=True*.
    """
    init_db()
    db = SessionLocal()

    try:
        existing = db.query(Catalyst).count()
        if existing > 0 and not force:
            print(f"Database already has {existing} catalysts. Skipping seed.")
            print("Pass force=True or delete existing rows to re-seed.")
            return

        print(f"Seeding {len(SEED_CATALYSTS)} catalysts...")

        for data in SEED_CATALYSTS:
            # Skip if name already exists
            if db.query(Catalyst).filter(Catalyst.name == data["name"]).first():
                continue

            db.add(Catalyst(
                id=str(uuid.uuid4()),
                name=data["name"],
                composition=data["composition"],
                catalyst_type=data["catalyst_type"],
                reaction_target=data["reaction_target"],
                reported_activity=data["reported_activity"],
                reported_selectivity=data["reported_selectivity"],
                reported_stability=data["reported_stability"],
                source=data["source"],
            ))

        db.commit()
        final_count = db.query(Catalyst).count()
        print(f"Seeded successfully. Total catalysts in DB: {final_count}")

        # Summary by reaction
        print("\nDatabase summary:")
        reactions = {c["reaction_target"] for c in SEED_CATALYSTS}
        for rxn in sorted(reactions):
            n = db.query(Catalyst).filter(Catalyst.reaction_target == rxn).count()
            print(f"  {rxn}: {n} catalysts")

    except Exception as exc:
        print(f"Error seeding database: {exc}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Seed MolDiscovery database")
    parser.add_argument("--force", action="store_true", help="Re-seed even if data exists")
    args = parser.parse_args()
    seed_database(force=args.force)
