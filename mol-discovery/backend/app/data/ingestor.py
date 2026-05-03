"""
DataIngestor — real DB operations (sync SQLAlchemy).
Loads catalysts and experiments into PostgreSQL / SQLite.
Falls back to synthetic data when the DB has no matching rows.
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from app.db.session import SessionLocal
from app.db.models import Catalyst, Experiment

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Synthetic fallback libraries (used only when DB is empty)
# ---------------------------------------------------------------------------

_ETHANOL_JET_KNOWN = [
    {"name": "H-ZSM-5 (Si/Al=25)",        "activity": 1.8,  "selectivity": 0.82, "stability": 340},
    {"name": "H-ZSM-5 (Si/Al=40)",        "activity": 1.6,  "selectivity": 0.79, "stability": 380},
    {"name": "H-Beta zeolite",             "activity": 1.4,  "selectivity": 0.75, "stability": 300},
    {"name": "SAPO-34",                    "activity": 1.2,  "selectivity": 0.71, "stability": 250},
    {"name": "ZSM-5 with Ga",             "activity": 2.4,  "selectivity": 0.88, "stability": 520},
    {"name": "SAPO-34 with Ni",           "activity": 2.1,  "selectivity": 0.85, "stability": 480},
    {"name": "Y-zeolite with Cu",         "activity": 1.9,  "selectivity": 0.81, "stability": 420},
    {"name": "MCM-41 with Pt",            "activity": 1.5,  "selectivity": 0.74, "stability": 280},
    {"name": "SSZ-13",                     "activity": 1.3,  "selectivity": 0.72, "stability": 310},
    {"name": "ZSM-5 with P modification", "activity": 1.7,  "selectivity": 0.80, "stability": 360},
    {"name": "H-ZSM-5 (Si/Al=15)",        "activity": 2.0,  "selectivity": 0.84, "stability": 400},
    {"name": "Ferrierite zeolite",         "activity": 1.1,  "selectivity": 0.68, "stability": 220},
    {"name": "ZSM-22",                     "activity": 1.35, "selectivity": 0.73, "stability": 290},
    {"name": "MCM-22",                     "activity": 1.55, "selectivity": 0.77, "stability": 330},
    {"name": "ZSM-5 with Zn (1 wt%)",     "activity": 2.2,  "selectivity": 0.86, "stability": 460},
]

_CO2_METHANOL_KNOWN = [
    {"name": "Cu/ZnO/Al2O3 (industrial)", "activity": 2.5, "selectivity": 0.90, "stability": 600},
    {"name": "Cu/ZnO/ZrO2",               "activity": 2.3, "selectivity": 0.88, "stability": 550},
    {"name": "In2O3",                      "activity": 1.8, "selectivity": 0.85, "stability": 480},
    {"name": "Pd/SiO2",                    "activity": 1.5, "selectivity": 0.78, "stability": 400},
    {"name": "Cu/CeO2",                    "activity": 1.9, "selectivity": 0.82, "stability": 430},
]

_GENERIC_KNOWN = [
    {
        "name":        f"Reference catalyst {i + 1}",
        "activity":    round(1.0 + i * 0.15, 2),
        "selectivity": round(0.70 + i * 0.02, 2),
        "stability":   200 + i * 20,
    }
    for i in range(10)
]


class DataIngestor:
    def __init__(self):
        self.db = SessionLocal()

    # ------------------------------------------------------------------
    # Catalyst retrieval
    # ------------------------------------------------------------------

    def fetch_known_catalysts(self, reaction: str, limit: int = 25) -> List[Dict]:
        """
        Return known catalysts for *reaction*.
        Queries the DB first (excluding ai_generated rows);
        pads with synthetic data when the DB has fewer than *limit* rows.
        """
        results: List[Dict] = []

        try:
            db_rows = (
                self.db.query(Catalyst)
                .filter(Catalyst.reaction_target.ilike(f"%{reaction[:40]}%"))
                .filter(Catalyst.source != "ai_generated")
                .limit(limit)
                .all()
            )
            for cat in db_rows:
                results.append({
                    "id":          str(cat.id),
                    "name":        cat.name,
                    "composition": cat.composition or {},
                    "activity":    cat.reported_activity,
                    "selectivity": cat.reported_selectivity,
                    "stability":   cat.reported_stability,
                    "source":      cat.source or "database",
                })
        except Exception as exc:
            log.warning("DB query failed, using synthetic data: %s", exc)

        # Pad with synthetic data if DB is sparse
        if len(results) < limit:
            synthetic = self._synthetic_catalysts(reaction)
            for i, s in enumerate(synthetic):
                if len(results) >= limit:
                    break
                s.setdefault("id", f"syn_{i}")
                results.append(s)

        return results[:limit]

    def _synthetic_catalysts(self, reaction: str) -> List[Dict]:
        rxn = reaction.lower()
        if "ethanol" in rxn and ("jet" in rxn or "fuel" in rxn):
            pool = _ETHANOL_JET_KNOWN
        elif "co2" in rxn and "methanol" in rxn:
            pool = _CO2_METHANOL_KNOWN
        else:
            pool = _GENERIC_KNOWN

        return [
            {
                "name":        t["name"],
                "composition": {"type": "zeolite"},
                "activity":    t["activity"],
                "selectivity": t["selectivity"],
                "stability":   t["stability"],
                "source":      "synthetic_demo",
                "type":        "known",
            }
            for t in pool
        ]

    # ------------------------------------------------------------------
    # Catalyst storage
    # ------------------------------------------------------------------

    def store_catalyst(self, data: Dict) -> str:
        """Persist a new catalyst record. Returns the new ID."""
        cat = Catalyst(
            id=str(uuid.uuid4()),
            name=data["name"],
            composition=data.get("composition", {}),
            catalyst_type=data.get("catalyst_type", "unknown"),
            reaction_target=data.get("reaction_target", ""),
            reported_activity=data.get("activity"),
            reported_selectivity=data.get("selectivity"),
            reported_stability=data.get("stability"),
            source=data.get("source", "manual"),
        )
        try:
            self.db.add(cat)
            self.db.commit()
            self.db.refresh(cat)
            return str(cat.id)
        except Exception as exc:
            self.db.rollback()
            log.error("Failed to store catalyst: %s", exc)
            return str(uuid.uuid4())

    # ------------------------------------------------------------------
    # Experiment storage
    # ------------------------------------------------------------------

    def store_experiment(self, data: Dict) -> str:
        """Persist a single experiment record. Returns the new ID."""
        exp = Experiment(
            id=str(uuid.uuid4()),
            candidate_id=data.get("candidate_id"),
            measured_activity=data.get("activity"),
            measured_selectivity=data.get("selectivity"),
            measured_stability=data.get("stability", 0),
            temperature=data.get("temperature", 350.0),
            pressure=data.get("pressure", 1.0),
            researcher=data.get("researcher", "unknown"),
            lab=data.get("lab"),
        )
        try:
            self.db.add(exp)
            self.db.commit()
            self.db.refresh(exp)
            return str(exp.id)
        except Exception as exc:
            self.db.rollback()
            log.error("Failed to store experiment: %s", exc)
            return str(uuid.uuid4())

    # ------------------------------------------------------------------
    # Bulk CSV import
    # ------------------------------------------------------------------

    def ingest_csv_from_dataframe(self, df: pd.DataFrame) -> int:
        """Bulk-import experiments from a pandas DataFrame. Returns row count."""
        count = 0
        for _, row in df.iterrows():
            self.store_experiment(row.to_dict())
            count += 1
        return count

    def ingest_csv_to_catalysts(self, file_path: str) -> int:
        """Bulk-import catalysts from a CSV file."""
        df = pd.read_csv(file_path)
        count = 0
        for _, row in df.iterrows():
            self.store_catalyst({
                "name":            row.get("name"),
                "composition":     {"elements": str(row.get("elements", "")).split(",")},
                "catalyst_type":   row.get("type", "heterogeneous"),
                "reaction_target": row.get("reaction", ""),
                "activity":        row.get("activity"),
                "selectivity":     row.get("selectivity"),
                "stability":       row.get("stability"),
                "source":          "csv_import",
            })
            count += 1
        return count

    def ingest_csv_to_experiments(self, file_path: str) -> int:
        """Bulk-import experiments from a CSV file."""
        df = pd.read_csv(file_path)
        count = 0
        for _, row in df.iterrows():
            self.store_experiment(row.to_dict())
            count += 1
        return count

    def ingest_csv(self, file_path: str) -> int:
        """Alias for ingest_csv_to_experiments (backward compat)."""
        return self.ingest_csv_to_experiments(file_path)

    def close(self):
        self.db.close()
