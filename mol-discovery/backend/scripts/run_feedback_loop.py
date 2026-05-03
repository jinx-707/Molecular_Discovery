#!/usr/bin/env python3
from backend.app.services.feedback.retraining_orchestrator import RetrainingOrchestrator
from backend.app.services.feedback.experiment_handler import ExperimentHandler

if __name__ == "__main__":
    handler = ExperimentHandler()
    orchestrator = RetrainingOrchestrator()
    
    print("Running daily feedback loop...")
    
    # Process new experiments (stub data)
    data = [{"smiles": "TiO2", "activity": 2.1, "selectivity": 0.87}]
    exp_id = handler.store_experiment(data)
    
    metrics = handler.compare_with_prediction(exp_id)
    if handler.flag_discrepancy(exp_id):
        print("Discrepancy flagged!")
    
    triggers = orchestrator.check_triggers()
    if triggers["triggers"]:
        print(f"Retraining triggered by: {triggers['triggers']}")
        orchestrator.execute_retraining("catalyst", data)
    
    print("Feedback loop complete")

