"""
DataIngestor – pulls data from external sources (OC20/OC22, Materials Project,
BRENDA, custom CSV) and stores records + vector embeddings.

All external API calls fall back to synthetic data when API keys are absent.
"""
from __future__ import annotations

import csv
import logging
import random
import string
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from ..core.config import settings
from ..db.models import Catalyst, Enzyme, Experiment
from ..db.session import AsyncSessionLocal

log = logging.getLogger(__name__)

EMBEDDING_DIM = 384

# ---------------------------------------------------------------------------
# Placeholder embedding – returns a random unit-normalised 384-dim vector.
# Replace body with real model call when available.
# ---------------------------------------------------------------------------

def get_embedding(text: str) -> List[float]:
    rng = np.random.default_rng(seed=abs(hash(text)) % (2**32))
    vec = rng.standard_normal(EMBEDDING_DIM).astype(np.float32)
    vec /= np.linalg.norm(vec) + 1e-9
    return vec.tolist()


# ---------------------------------------------------------------------------
# Synthetic data helpers
# ---------------------------------------------------------------------------

_ELEMENTS = ["Fe", "Ni", "Co", "Cu", "Pt", "Pd", "Ru", "Ir", "Mo", "W"]
_REACTION_TYPES = ["CO2 reduction", "N2 fixation", "H2 evolution", "O2 reduction", "methane oxidation"]
_ORGANISMS = ["E. coli", "S. cerevisiae", "B. subtilis", "T. thermophilus", "P. putida"]
_EC_NUMBERS = ["1.1.1.1", "1.2.1.2", "2.7.1.1", "3.1.1.1", "4.1.1.1"]
_SOURCES_CAT = ["OC20", "OC22", "materials_project", "internal"]
_SOURCES_ENZ = ["brenda", "uniprot", "internal"]


def _rand_str(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


def _synthetic_catalyst(idx: int) -> Dict[str, Any]:
    elements = random.sample(_ELEMENTS, k=random.randint(1, 3))
    fractions = np.random.dirichlet(np.ones(len(elements))).tolist()
    return {
        "name": f"Cat-{idx:04d}-{''.join(elements)}",
        "smiles": f"[{''.join(elements[0])}]",
        "inchi_key": _rand_str(14) + "-" + _rand_str(10) + "-N",
        "composition": dict(zip(elements, fractions)),
        "formula": "".join(f"{e}{random.randint(1,4)}" for e in elements),
        "molecular_weight": round(random.uniform(50, 500), 2),
        "reaction_type": random.choice(_REACTION_TYPES),
        "temperature_k": round(random.uniform(273, 1073), 1),
        "pressure_bar": round(random.uniform(1, 100), 2),
        "ph": round(random.uniform(1, 13), 1),
        "source": random.choice(_SOURCES_CAT),
        "external_id": f"ext-{_rand_str(6)}",
        "conditions": {"atmosphere": random.choice(["N2", "Ar", "air", "H2"])},
        "descriptors": {"morgan_fp_density": round(random.random(), 4)},
    }


def _synthetic_enzyme(idx: int) -> Dict[str, Any]:
    seq_len = random.randint(100, 800)
    aas = "ACDEFGHIKLMNPQRSTVWY"
    sequence = "".join(random.choices(aas, k=seq_len))
    return {
        "name": f"Enz-{idx:04d}-{_rand_str(4)}",
        "gene_name": f"gene_{_rand_str(4).lower()}",
        "organism": random.choice(_ORGANISMS),
        "amino_acid_sequence": sequence,
        "sequence_length": seq_len,
        "uniprot_id": f"P{random.randint(10000, 99999)}",
        "pdb_id": _rand_str(4),
        "ec_number": random.choice(_EC_NUMBERS),
        "is_wildtype": True,
        "km_mm": round(random.uniform(0.01, 10), 4),
        "kcat_per_s": round(random.uniform(0.1, 1000), 2),
        "source": random.choice(_SOURCES_ENZ),
        "external_id": f"ext-{_rand_str(6)}",
        "mutations": [],
        "cofactors": random.sample(["NAD+", "NADH", "FAD", "ATP", "CoA"], k=random.randint(0, 2)),
    }


def _synthetic_experiment(catalyst_id: Optional[str], enzyme_id: Optional[str]) -> Dict[str, Any]:
    return {
        "catalyst_id": catalyst_id,
        "enzyme_id": enzyme_id,
        "activity": round(random.uniform(0.01, 100), 4),
        "selectivity": round(random.uniform(0, 1), 4),
        "stability": round(random.uniform(1, 500), 2),
        "yield_": round(random.uniform(0, 1), 4),
        "conversion": round(random.uniform(0, 1), 4),
        "temperature_k": round(random.uniform(273, 473), 1),
        "pressure_bar": round(random.uniform(1, 50), 2),
        "ph": round(random.uniform(4, 10), 1),
        "reaction_time_h": round(random.uniform(0.5, 48), 1),
        "lab": "GPS-Lab-1",
        "operator": f"operator_{random.randint(1, 5)}",
        "batch_id": f"BATCH-{_rand_str(6)}",
        "measured_at": datetime.utcnow(),
        "conditions": {},
    }


# ---------------------------------------------------------------------------
# Qdrant helpers
# ---------------------------------------------------------------------------

def _qdrant_client():
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import Distance, VectorParams

        client = QdrantClient(settings.QDRANT_URL)
        for collection in ("catalysts", "enzymes"):
            existing = {c.name for c in client.get_collections().collections}
            if collection not in existing:
                client.create_collection(
                    collection_name=collection,
                    vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
                )
        return client
    except Exception as exc:
        log.warning("Qdrant unavailable – skipping vector store: %s", exc)
        return None


# ---------------------------------------------------------------------------
# DataIngestor
# ---------------------------------------------------------------------------

class DataIngestor:
    """Fetches, validates, and stores molecular data into Postgres + Qdrant."""

    # ------------------------------------------------------------------
    # Public fetch methods
    # ------------------------------------------------------------------

    async def fetch_open_catalyst(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Pull from OC20/OC22 dataset API.
        Falls back to synthetic data when OPENCATALYST_MODEL_PATH is not set
        or the API is unreachable.
        """
        try:
            model_path = getattr(settings, "OPENCATALYST_MODEL_PATH", None)
            if not model_path or model_path == "/models/opencatalyst":
                raise EnvironmentError("OC20/OC22 model path not configured")

            # Real implementation would use the OCP Python API:
            # from ocpmodels.datasets import LmdbDataset
            # dataset = LmdbDataset({"src": model_path})
            # records = [self._oc_record_to_dict(dataset[i]) for i in range(min(limit, len(dataset)))]
            raise NotImplementedError("Real OC20 fetch not yet wired")

        except Exception as exc:
            log.warning("fetch_open_catalyst falling back to synthetic data: %s", exc)
            return [_synthetic_catalyst(i) for i in range(limit)]

    async def fetch_materials_project(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Pull catalyst structures from the Materials Project REST API.
        Falls back to synthetic data when MP_API_KEY is absent.
        """
        try:
            api_key = getattr(settings, "MP_API_KEY", None)
            if not api_key:
                raise EnvironmentError("MP_API_KEY not set")

            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "https://api.materialsproject.org/materials/summary/",
                    params={"_limit": limit, "fields": "material_id,formula_pretty,structure"},
                    headers={"X-API-KEY": api_key},
                )
                resp.raise_for_status()
                items = resp.json().get("data", [])
            return [self._mp_record_to_dict(item, idx) for idx, item in enumerate(items)]

        except Exception as exc:
            log.warning("fetch_materials_project falling back to synthetic data: %s", exc)
            return [_synthetic_catalyst(i) for i in range(limit)]

    async def fetch_brenda(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Pull enzyme kinetic data from BRENDA via SOAP API.
        Falls back to synthetic data when BRENDA_API_KEY is absent.
        """
        try:
            api_key = settings.BRENDA_API_KEY
            if not api_key or api_key == "your_brenda_key":
                raise EnvironmentError("BRENDA_API_KEY not set")

            # Real implementation would use zeep or suds-jurko:
            # from zeep import Client
            # client = Client("https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl")
            # ...
            raise NotImplementedError("Real BRENDA SOAP fetch not yet wired")

        except Exception as exc:
            log.warning("fetch_brenda falling back to synthetic data: %s", exc)
            return [_synthetic_enzyme(i) for i in range(limit)]

    async def ingest_custom_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse an internal GPS experiment CSV.

        Expected columns (all optional except measured_at):
            catalyst_id, enzyme_id, activity, selectivity, stability,
            yield, conversion, temperature_k, pressure_bar, ph,
            reaction_time_h, lab, operator, batch_id, measured_at
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV not found: {file_path}")

        records: List[Dict[str, Any]] = []
        with path.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                record: Dict[str, Any] = {}
                for key, value in row.items():
                    if value == "":
                        record[key] = None
                    else:
                        try:
                            record[key] = float(value)
                        except (ValueError, TypeError):
                            record[key] = value
                if "measured_at" not in record or record["measured_at"] is None:
                    record["measured_at"] = datetime.utcnow()
                else:
                    record["measured_at"] = datetime.fromisoformat(str(record["measured_at"]))
                records.append(record)

        log.info("Parsed %d rows from %s", len(records), file_path)
        return records

    # ------------------------------------------------------------------
    # Storage methods
    # ------------------------------------------------------------------

    async def store_catalysts(self, records: List[Dict[str, Any]]) -> List[str]:
        """Persist catalyst records to Postgres. Returns list of inserted IDs."""
        ids: List[str] = []
        async with AsyncSessionLocal() as session:
            for rec in records:
                rec.setdefault("embedding", get_embedding(rec.get("name", "") + str(rec.get("smiles", ""))))
                catalyst = Catalyst(id=uuid.uuid4(), **{k: v for k, v in rec.items() if hasattr(Catalyst, k)})
                session.add(catalyst)
                ids.append(str(catalyst.id))
            await session.commit()
        log.info("Stored %d catalysts", len(ids))
        return ids

    async def store_enzymes(self, records: List[Dict[str, Any]]) -> List[str]:
        """Persist enzyme records to Postgres. Returns list of inserted IDs."""
        ids: List[str] = []
        async with AsyncSessionLocal() as session:
            for rec in records:
                rec.setdefault("embedding", get_embedding(rec.get("name", "") + str(rec.get("amino_acid_sequence", "")[:50])))
                enzyme = Enzyme(id=uuid.uuid4(), **{k: v for k, v in rec.items() if hasattr(Enzyme, k)})
                session.add(enzyme)
                ids.append(str(enzyme.id))
            await session.commit()
        log.info("Stored %d enzymes", len(ids))
        return ids

    async def store_experiments(self, records: List[Dict[str, Any]]) -> List[str]:
        """Persist experiment records to Postgres."""
        ids: List[str] = []
        async with AsyncSessionLocal() as session:
            for rec in records:
                # Map yield_ alias
                if "yield_" in rec:
                    rec["yield_"] = rec.pop("yield_")
                exp = Experiment(id=uuid.uuid4(), **{k: v for k, v in rec.items() if hasattr(Experiment, k)})
                session.add(exp)
                ids.append(str(exp.id))
            await session.commit()
        log.info("Stored %d experiments", len(ids))
        return ids

    async def vectorize_and_store(
        self,
        catalyst_records: Optional[List[Dict[str, Any]]] = None,
        enzyme_records: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Generate embeddings for all records and upsert into Qdrant.
        Embeddings are also stored in the Postgres ARRAY column via store_* methods.
        """
        from qdrant_client.http.models import PointStruct

        qdrant = _qdrant_client()

        if catalyst_records:
            points = []
            for rec in catalyst_records:
                text = rec.get("name", "") + " " + str(rec.get("smiles", "")) + " " + str(rec.get("reaction_type", ""))
                embedding = get_embedding(text)
                rec["embedding"] = embedding
                points.append(
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding,
                        payload={
                            "name": rec.get("name"),
                            "formula": rec.get("formula"),
                            "reaction_type": rec.get("reaction_type"),
                            "source": rec.get("source"),
                        },
                    )
                )
            if qdrant and points:
                qdrant.upsert(collection_name="catalysts", points=points)
                log.info("Upserted %d catalyst vectors to Qdrant", len(points))

        if enzyme_records:
            points = []
            for rec in enzyme_records:
                text = rec.get("name", "") + " " + str(rec.get("ec_number", "")) + " " + str(rec.get("organism", ""))
                embedding = get_embedding(text)
                rec["embedding"] = embedding
                points.append(
                    PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding,
                        payload={
                            "name": rec.get("name"),
                            "ec_number": rec.get("ec_number"),
                            "organism": rec.get("organism"),
                            "source": rec.get("source"),
                        },
                    )
                )
            if qdrant and points:
                qdrant.upsert(collection_name="enzymes", points=points)
                log.info("Upserted %d enzyme vectors to Qdrant", len(points))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _mp_record_to_dict(item: Dict[str, Any], idx: int) -> Dict[str, Any]:
        return {
            "name": item.get("formula_pretty", f"MP-{idx}"),
            "formula": item.get("formula_pretty"),
            "external_id": item.get("material_id"),
            "source": "materials_project",
            "composition": {},
            "conditions": {},
            "descriptors": {},
        }
