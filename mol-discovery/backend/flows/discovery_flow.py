from prefect import flow, task
from prefect.task_runners import SequentialTaskRunner
from typing import List, Dict
from backend.app.ml.catalyst_generator import CatalystDiffusionGenerator
from backend.app.ml.catalyst_predictor import CatalystGNNPredictor
from backend.app.services.vector_search import client as vector_client
from backend.app.simulation.energy import ReactionEnergyEstimator

@task(cache_key_fn=lambda reaction, type: f"known_{reaction[:50]}_{type}", cache_expiration=3600)
def retrieve_known(reaction: str, type: str) -> List[str]:
    """Query vector DB for similar reactions"""
    try:
        results = vector_client.search("reactions", reaction, limit=10)
        return [hit.payload['smiles'] for hit in results]
    except:
        return ["TiO2", "ZrO2"]  # fallback

@task
def generate_novel(reaction: str, known: List[str], constraints: Dict) -> List[str]:
    gen = CatalystDiffusionGenerator()
    return gen.generate(reaction, n_samples=20)

@task
def predict_all(candidates: List[str]) -> List[Dict]:
    predictor = CatalystGNNPredictor()
    inputs = [{"smiles": c} for c in candidates]
    return predictor.predict(inputs)

@task
def rank_and_store(predictions: List[Dict], run_id: str):
    """Stub store/rank"""
    scored = sorted(predictions, key=lambda x: x['activity'], reverse=True)
    print(f"Stored {len(scored)} candidates for run {run_id}")
    return run_id

@flow(task_runner=SequentialTaskRunner(), log_prints=True)
def discovery_pipeline(reaction: str, constraints: Dict = None, type: str = "catalyst"):
    """Full discovery workflow"""
    known = retrieve_known(reaction, type)
    novel = generate_novel(reaction, known, constraints or {})
    preds = predict_all(novel)
    run_id = f"run_{reaction[:8]}"
    rank_and_store(preds, run_id)
    return {"run_id": run_id, "top_score": preds[0]['activity'] if preds else 0}

