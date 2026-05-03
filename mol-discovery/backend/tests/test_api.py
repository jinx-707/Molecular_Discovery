import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_discovery_start():
    response = client.post("/api/discovery/start", json={"reaction": "CO2+H2", "type": "catalyst"})
    assert response.status_code == 200
    assert "run_id" in response.json()

def test_parse_reaction():
    response = client.post("/api/reaction/parse", json={"natural_language": "CO2 hydrogenation"})
    assert response.status_code == 200
    assert "smiles" in response.json()

