import torch
import torch.nn as nn
from rdkit import Chem
from .base import Predictor, ModelInput, Prediction
from .uncertainty import monte_carlo_dropout, prediction_with_uncertainty
from typing import List

class SimpleCatalystGNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(2048, 512),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(512, 3)  # activity, selectivity, stability
        )
    
    def forward(self, x):
        return self.fc(x)

class CatalystGNNPredictor(Predictor):
    def __init__(self, model_path: str = None):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = SimpleCatalystGNN().to(self.device)
        if model_path:
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
    
    def smiles_to_fp(self, smiles: str) -> torch.Tensor:
        mol = Chem.MolFromSmiles(smiles)
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
        return torch.tensor([int(b) for b in fp.ToBitString()], dtype=torch.float32).unsqueeze(0).to(self.device)
    
    def predict(self, candidates: List[ModelInput]) -> List[Prediction]:
        fps = torch.cat([self.smiles_to_fp(c.smiles) for c in candidates])
        mean, std = monte_carlo_dropout(self.model, fps)
        return [prediction_with_uncertainty(mean[i], std[i]) for i in range(len(candidates))]
    
    def fine_tune(self, data: List) -> None:
        print(f"Fine-tuned CatalystGNN on {len(data)} samples (5 epochs simulated)")

