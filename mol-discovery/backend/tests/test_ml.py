import pytest
from backend.app.ml.catalyst_predictor import CatalystGNNPredictor
from backend.app.ml.base import ModelInput

def test_catalyst_predictor():
    predictor = CatalystGNNPredictor()
    candidates = [ModelInput(smiles="TiO2")]
    results = predictor.predict(candidates)
    assert len(results) == 1
    assert 0 < results[0].activity < 10
    assert 0 <= results[0].selectivity <= 1
    assert results[0].uncertainty >= 0

def test_generator():
    from backend.app.ml.catalyst_generator import CatalystDiffusionGenerator
    gen = CatalystDiffusionGenerator()
    results = gen.generate(condition="CO2 + H2 -> CH3OH", n_samples=3)
    assert len(results) == 3
    assert all(len(r) > 0 for r in results)

if __name__ == "__main__":
    pytest.main(["-v"])

