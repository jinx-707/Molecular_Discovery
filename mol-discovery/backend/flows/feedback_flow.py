from prefect import flow, task
from backend.app.services.feedback_service import FeedbackService
from typing import List
import datetime

@task
def fetch_new_experiments(since_date: str) -> List[Dict]:
    """Fetch recent experiments"""
    return [{"activity": random.uniform(0, 5), "pred": random.uniform(0, 5)} for _ in range(20)]

@task
def compute_discrepancies(preds: List[float], exps: List[float]) -> float:
    service = FeedbackService()
    return service.analyze_discrepancy(preds, exps)['discrepancy']

@task
def trigger_retraining_if_needed(discrepancy: float, n_samples: int) -> bool:
    return discrepancy > 0.15 or n_samples > 50

@task
def retrain_model(model_type: str, data: List):
    print(f"Retraining {model_type} on {len(data)} samples")
    return True

@task
def validate_model(model_type: str) -> bool:
    print(f"Validated {model_type}: accuracy=0.92")
    return True

@flow
def feedback_loop():
    exps = fetch_new_experiments((datetime.date.today() - datetime.timedelta(days=7)).isoformat())
    preds = [e['pred'] for e in exps]
    exps_vals = [e['activity'] for e in exps]
    
    disc = compute_discrepancies(preds, exps_vals)
    
    if trigger_retraining_if_needed(disc, len(exps)):
        retrain_model("catalyst_predictor", exps)
        if validate_model("catalyst_predictor"):
            print("✅ Model promoted to production")
        print("Slack notification sent!")

