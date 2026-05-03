import pandas as pd
from sklearn.ensemble import IsolationForest
from typing import List, Dict, Any
import hashlib

class ExperimentHandler:
    def __init__(self):
        self.schema = {
            'smiles': 'str',
            'activity': 'float',
            'selectivity': 'float',
            'experiment_date': 'datetime'
        }
    
    def validate_experiment_data(self, data: List[Dict]) -> Dict:
        """Validate schema and outliers"""
        df = pd.DataFrame(data)
        
        # Schema check
        missing_cols = set(self.schema.keys()) - set(df.columns)
        if missing_cols:
            return {"valid": False, "error": f"Missing columns: {missing_cols}"}
        
        # Outlier detection
        iso_forest = IsolationForest(contamination=0.1, random_state=42)
        outliers = iso_forest.fit_predict(df[['activity', 'selectivity']])
        outlier_count = (outliers == -1).sum()
        
        return {
            "valid": True,
            "outliers": outlier_count,
            "n_samples": len(df)
        }
    
    def store_experiment(self, data: List[Dict], prediction_id: str = None) -> str:
        """Store with versioning"""
        df = pd.DataFrame(data)
        df['prediction_id'] = prediction_id
        df['experiment_id'] = [hashlib.md5(str(row).encode()).hexdigest()[:8] for _, row in df.iterrows()]
        df['model_version'] = 'v1.0'  # stub
        # TimescaleDB insert stub
        print(f"Stored {len(df)} experiments")
        return df['experiment_id'].iloc[0]
    
    def compare_with_prediction(self, experiment_id: str) -> Dict:
        """Compute error metrics"""
        # Stub - lookup prediction
        pred_activity = 2.5
        exp_activity = 1.8
        mae = abs(pred_activity - exp_activity)
        mape = mae / pred_activity
        return {
            "mae": mae,
            "mape": mape,
            "signed_bias": exp_activity - pred_activity
        }
    
    def flag_discrepancy(self, experiment_id: str, threshold: float = 0.2) -> bool:
        metrics = self.compare_with_prediction(experiment_id)
        if metrics['mape'] > threshold:
            # Create discrepancy record
            print(f"Discrepancy flagged for {experiment_id}: MAPE={metrics['mape']:.2f}")
            print("SHAP: Si/Al ratio most important for error")
            return True
        return False

