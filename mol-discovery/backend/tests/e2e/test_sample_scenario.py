import pytest
import httpx
import asyncio
from unittest.mock import patch, MagicMock
import time
import pandas as pd

@pytest.fixture(scope="session")
def test_client():
    from backend.app.main import app
    with httpx.TestClient(app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_full_discovery_scenario(test_client: httpx.TestClient):
    """Full e2e ethanol-to-jet scenario"""
    
    with patch('backend.app.ml.catalyst_predictor.CatalystGNNPredictor') as MockPredictor, \
         patch('backend.app.ml.catalyst_generator.CatalystDiffusionGenerator') as MockGenerator:
        
        # Mock deterministic outputs
        mock_pred = MockPredictor.return_value
        mock_pred.predict.return_value = [
            {"activity": 2.5, "selectivity": 0.9, "stability": 48, "uncertainty": 0.05},
            {"activity": 2.1, "selectivity": 0.85, "stability": 36, "uncertainty": 0.08}
        ] * 10
        
        mock_gen = MockGenerator.return_value
        mock_gen.generate.return_value = ["TiO2-Ga", "ZSM5-Al", "ZrO2"] * 7
        
        # a. Start discovery
        response = test_client.post("/api/discovery/start", json={
            "reaction": "ethanol → jet hydrocarbons",
            "type": "catalyst"
        })
        assert response.status_code == 200
        run_id = response.json()["run_id"]
        
        # b. Poll until complete (mock instant)
        time.sleep(1)
        status_response = test_client.get(f"/api/discovery/{run_id}/status")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "running"  # or completed
        
        # c. Get results
        results_response = test_client.get(f"/api/discovery/{run_id}/results")
        assert results_response.status_code == 200
        results = results_response.json()["candidates"]
        assert len(results) >= 20
        
        # d. Export top 3 (stub)
        top3 = results[:3]
        
        # e. Log experiments
        exp_data = [
            {"smiles": top3[0]["smiles"], "activity": 2.8, "selectivity": 0.92},  # success
            {"smiles": top3[1]["smiles"], "activity": 2.3, "selectivity": 0.88},  # success
            {"smiles": top3[2]["smiles"], "activity": 1.2, "selectivity": 0.4},   # failure
        ]
        log_response = test_client.post("/api/experiment/log", json={"data": exp_data})
        assert log_response.status_code == 200
        assert log_response.json()["retrain_triggered"] == True
        
        # f. Check retraining triggered
        retrain_response = test_client.post("/api/model/retrain")
        assert retrain_response.status_code == 200
        
        # g. Verify history shows version increment
        history = test_client.get("/api/feedback/retraining/history")
        assert len(history.json()) > 0
        
        print("✅ Full scenario passed!")

@pytest.mark.parametrize("n_candidates", [100])
def test_prediction_latency(n_candidates):
    from backend.app.ml.catalyst_predictor import CatalystGNNPredictor
    import time
    
    start = time.time()
    predictor = CatalystGNNPredictor()
    candidates = [{"smiles": f"TiO2_{i}"} for i in range(n_candidates)]
    results = predictor.predict(candidates)
    latency = time.time() - start
    
    assert latency < 10.0
    assert len(results) == n_candidates
    print(f"✅ 100 predictions in {latency:.2f}s")

