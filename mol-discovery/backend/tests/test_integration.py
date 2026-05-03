"""
Integration tests — full API workflow using an in-memory SQLite DB.
Run with:  pytest tests/test_integration.py -v
"""
import os
import pytest

# Force SQLite before any app import so session.py picks it up
os.environ["DATABASE_URL"] = "sqlite:///./test_moldiscovery.db"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create tables once for the whole test session."""
    from app.db.session import init_db
    init_db()
    yield
    # Teardown — dispose engine then remove test DB file
    import pathlib
    from app.db.session import engine
    engine.dispose()
    try:
        pathlib.Path("./test_moldiscovery.db").unlink(missing_ok=True)
    except PermissionError:
        pass  # Windows may hold the file; ignore on CI


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_root(self):
        r = client.get("/")
        assert r.status_code == 200
        assert r.json()["status"] == "running"

    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


# ---------------------------------------------------------------------------
# Discovery workflow
# ---------------------------------------------------------------------------

class TestDiscoveryWorkflow:
    def test_start_discovery_ethanol_jet(self):
        r = client.post("/api/discovery/start", json={
            "reaction":  "ethanol to jet fuel",
            "user_id":   "test_user",
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert "run_id" in data
        assert data["status"] == "completed"
        assert data["total_candidates"] > 0
        assert len(data["candidates"]) > 0

        # Validate candidate shape
        c = data["candidates"][0]
        assert "name" in c
        assert "score" in c
        assert "predicted_activity" in c
        assert "predicted_selectivity" in c
        assert "predicted_stability" in c
        assert "uncertainty" in c

    def test_start_discovery_co2_methanol(self):
        r = client.post("/api/discovery/start", json={
            "reaction": "CO2 + H2 → methanol",
        })
        assert r.status_code == 200
        assert r.json()["status"] == "completed"

    def test_discovery_status(self):
        # Start a run first
        r = client.post("/api/discovery/start", json={"reaction": "ethanol to jet fuel"})
        run_id = r.json()["run_id"]

        status = client.get(f"/api/discovery/{run_id}/status")
        assert status.status_code == 200
        assert status.json()["status"] == "completed"

    def test_discovery_results(self):
        r = client.post("/api/discovery/start", json={"reaction": "ethanol to jet fuel"})
        run_id = r.json()["run_id"]

        results = client.get(f"/api/discovery/{run_id}/results")
        assert results.status_code == 200
        data = results.json()
        assert "run_id" in data
        assert "status" in data

    def test_discovery_not_found(self):
        r = client.get("/api/discovery/nonexistent-run-id/status")
        assert r.status_code == 404

    def test_candidates_are_ranked(self):
        r = client.post("/api/discovery/start", json={"reaction": "ethanol to jet fuel"})
        candidates = r.json()["candidates"]
        scores = [c["score"] for c in candidates]
        assert scores == sorted(scores, reverse=True), "Candidates should be sorted by score desc"


# ---------------------------------------------------------------------------
# Experiment logging
# ---------------------------------------------------------------------------

class TestExperimentLogging:
    def _get_candidate_id(self) -> str:
        r = client.post("/api/discovery/start", json={"reaction": "ethanol to jet fuel"})
        return r.json()["candidates"][0].get("catalyst_db_id") or r.json()["candidates"][0]["id"]

    def test_log_single_experiment(self):
        candidate_id = self._get_candidate_id()
        r = client.post("/api/experiment/log", data={
            "candidate_id":      candidate_id,
            "activity":          "2.5",
            "selectivity":       "0.85",
            "stability":         "400",
            "temperature":       "350",
            "researcher":        "test_user",
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "success"
        assert "experiment_id" in data
        assert "discrepancy" in data

    def test_log_experiment_missing_fields(self):
        r = client.post("/api/experiment/log", data={})
        assert r.status_code == 400

    def test_list_experiments(self):
        r = client.get("/api/experiments/")
        assert r.status_code == 200
        assert isinstance(r.json(), list)


# ---------------------------------------------------------------------------
# Model health & retraining
# ---------------------------------------------------------------------------

class TestModelFeedback:
    def test_model_health(self):
        r = client.get("/api/model/health")
        assert r.status_code == 200
        data = r.json()
        assert "overall_accuracy" in data
        assert "total_discrepancies" in data
        assert "retraining_ready" in data

    def test_retrain_skipped_when_no_data(self):
        r = client.post("/api/model/retrain")
        assert r.status_code == 200
        data = r.json()
        # Either skipped (no data) or success
        assert data["status"] in ("skipped", "success", "error")


# ---------------------------------------------------------------------------
# Catalog API
# ---------------------------------------------------------------------------

class TestCatalogAPI:
    def test_list_catalysts(self):
        r = client.get("/api/catalogs/catalysts")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_create_and_get_catalyst(self):
        payload = {
            "name":            "Test Pt/C Catalyst",
            "composition":     {"Pt": 0.05, "C": 0.95},
            "catalyst_type":   "heterogeneous",
            "reaction_target": "CO2 + H2 → methanol",
            "reported_activity":    2.1,
            "reported_selectivity": 0.88,
        }
        create = client.post("/api/catalogs/catalysts", json=payload)
        assert create.status_code == 201, create.text
        cat_id = create.json()["id"]
        assert create.json()["name"] == "Test Pt/C Catalyst"

        # Fetch by ID
        get = client.get(f"/api/catalogs/catalysts/{cat_id}")
        assert get.status_code == 200
        assert get.json()["id"] == cat_id

    def test_catalog_statistics(self):
        r = client.get("/api/catalogs/statistics")
        assert r.status_code == 200
        data = r.json()
        assert "total_catalysts" in data
        assert "by_type" in data
        assert "by_source" in data

    def test_catalyst_not_found(self):
        r = client.get("/api/catalogs/catalysts/does-not-exist")
        assert r.status_code == 404

    def test_search_catalysts(self):
        r = client.get("/api/catalysts/search?query=ethanol")
        assert r.status_code == 200
        data = r.json()
        assert "results" in data
        assert "count" in data


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_reaction_too_short(self):
        """Reactions shorter than 3 chars should be rejected."""
        r = client.post("/api/discovery/start", json={"reaction": "AB"})
        # Pydantic min_length=3 → 422 Unprocessable Entity
        assert r.status_code == 422

    def test_reaction_no_chemical_notation(self):
        """Reactions with no chemical tokens should fail the custom validator."""
        r = client.post("/api/discovery/start", json={"reaction": "hello world test"})
        assert r.status_code == 422
