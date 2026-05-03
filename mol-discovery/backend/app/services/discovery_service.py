from typing import Dict
import asyncio
from ..ml.catalyst_generator import CatalystDiffusionGenerator
from ..ml.catalyst_predictor import CatalystGNNPredictor
from ..simulation.energy import ReactionEnergyEstimator
from ..simulation.validator import StructureValidator

class DiscoveryService:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.generator = CatalystDiffusionGenerator()
        self.predictor = CatalystGNNPredictor()
        self.energy = ReactionEnergyEstimator()
        self.validator = StructureValidator()
    
    async def execute(self, reaction: str, model_type: str):
        # Step 1: Generate
        candidates = self.generator.generate(condition=reaction, n_samples=20)
        
        # Step 2: Predict
        preds = self.predictor.predict(candidates)
        
        # Step 3: Energy profile
        profiles = [self.energy.get_energy_profile(reaction, c) for c in candidates]
        
        # Step 4: Validate
        validations = [self.validator.validate_catalyst(c) for c in candidates]
        
        # Step 5: Rank (score = pred + energy + valid)
        scored = list(zip(candidates, preds, profiles, validations))
        scored.sort(key=lambda x: x[1][0].activity, reverse=True)
        
        # Store results (stub)
        print(f"Discovery {self.run_id} complete: top score {scored[0][1][0].activity}")

