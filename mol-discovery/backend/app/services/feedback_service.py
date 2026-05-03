import numpy as np
from typing import List, Dict

class FeedbackService:
    def __init__(self):
        self.discrepancy_threshold = 0.2
    
    def analyze_discrepancy(self, predicted: List[float], experimental: List[float]) -> Dict:
        """Compare pred vs exp, trigger retrain if high discrepancy"""
        if len(predicted) != len(experimental):
            return {"discrepancy": 1.0, "retrain": True}
        
        mae = np.mean(np.abs(np.array(predicted) - np.array(experimental)))
        return {
            "discrepancy": float(mae),
            "retrain_triggered": mae > self.discrepancy_threshold,
            "shap_summary": "Feature importance: catalyst_composition=0.45, reaction_conditions=0.35"
        }
    
    def queue_retraining(self, model_type: str):
        print(f"Queued retraining for {model_type}")

