import pytest
import time
from backend.app.ml.catalyst_predictor import CatalystGNNPredictor
from backend.app.ml.base import ModelInput

@pytest.mark.parametrize("n_candidates", [100])
def test_prediction_latency(n_candidates):
    predictor = CatalystGNNPredictor()
    candidates = [ModelInput(smiles=f"Candidate_{i}") for i in range(n_candidates)]
    
    start_time = time.time()
    results = predictor.predict(candidates)
    latency = time.time() - start_time
    
    assert latency < 10.0, f"Latency {latency:.2f}s > 10s limit"
    assert len(results) == n_candidates
    print(f"✅ {n_candidates} predictions in {latency:.2f}s")

