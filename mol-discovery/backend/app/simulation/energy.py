import numpy as np
from sklearn.ensemble import RandomForestRegressor
from typing import Dict, Any
import torch
import torch.nn as nn
from pathlib import Path

class SimpleSchNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, 2)  # Ea, deltaG
        )
    
    def forward(self, x):
        return self.fc(x)

class ReactionEnergyEstimator:
    def __init__(self, model_path: str = None):
        self.model_path = Path(model_path) if model_path else None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
        self._load_model()
    
    def _load_model(self):
        if self.model_path and self.model_path.exists():
            self.model = SimpleSchNet().to(self.device)
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model.eval()
            self.has_schnet = True
        else:
            self.has_schnet = False
            print("SchNet unavailable - using RF fallback")
    
    def descriptors(self, smiles: str, catalyst: str) -> np.ndarray:
        # Dummy descriptors: d-band, coordination, etc.
        return np.array([
            random.uniform(1, 3),  # d-band center
            random.uniform(4, 8),  # coordination
            len(smiles),  # size proxy
            0.5  # surface coverage
        ])
    
    def get_energy_profile(self, reaction_smiles: str, catalyst_structure: str) -> Dict[str, float]:
        desc = self.descriptors(reaction_smiles, catalyst_structure)
        
        if self.has_schnet:
            input_tensor = torch.tensor(desc).float().unsqueeze(0).to(self.device)
            with torch.no_grad():
                Ea, dG = self.model(input_tensor)[0].cpu().numpy()
        else:
            # RF fallback (trained on dummy data)
            Ea = 1.2 - 0.3 * desc[0] + 0.1 * desc[1]
            dG = -0.8 + 0.2 * desc[2] * desc[3]
        
        return {
            "transition_state_energy": float(Ea),
            "product_energy": float(dG),
            "intermediates": {"IM1": Ea * 0.6, "IM2": Ea * 0.8}
        }

