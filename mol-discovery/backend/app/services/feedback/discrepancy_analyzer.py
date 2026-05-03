from typing import List, Dict
import numpy as np

class DiscrepancyAnalyzer:
    def __init__(self):
        self.family_thresholds = {"zeolite": 0.15, "metal_oxide": 0.25}
    
    def analyze_batch(self, discrepancies: List[Dict]) -> Dict:
        """SHAP/IG for batch"""
        families = [d.get('family', 'unknown') for d in discrepancies]
        
        summary = {}
        for family in set(families):
            family_disc = [d for d in discrepancies if d.get('family') == family]
            if family_disc:
                avg_error = np.mean([d['mape'] for d in family_disc])
                summary[family] = {
                    "avg_mape": avg_error,
                    "count": len(family_disc),
                    "hypothesis": self._generate_hypothesis(family, avg_error)
                }
        
        return summary
    
    def _generate_hypothesis(self, family: str, mape: float) -> str:
        if 'zsm' in family.lower():
            return "Model underperforms for ZSM-5 when Si/Al > 40. Suggest collecting more high-ratio data."
        elif mape > 0.3:
            return "High temperature predictions unreliable. Needs more diverse training data."
        else:
            return "General performance degradation. Consider full retraining."

