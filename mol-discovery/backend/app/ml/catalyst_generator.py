import random
from typing import List
from .base import Generator, GenerationInput

# Known good catalysts
KNOWN_CATALYSTS = [
    "TiO2", 
    "ZrO2", 
    "Ga2O3", 
    "Al2O3", 
    "Zeolite-HZSM5",
    "[Pt]/CeO2"
]

ELEMENT_SUBS = {
    'Ti': ['Zr', 'Hf'],
    'Zr': ['Ti', 'Hf'],
    'Ga': ['Al', 'In'],
    'Al': ['Ga', 'B'],
    'Pt': ['Pd', 'Rh']
}

class CatalystDiffusionGenerator(Generator):
    def __init__(self):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
    
    def generate(self, condition: GenerationInput, n_samples: int = 10) -> List[str]:
        if self.device == 'cuda':
            # Diffusion stub - return dummy SMILES
            return ["C[Pt+2].[O-]C(=O)[O-]", "[Pd+2].[O-]C(=O)[O-]"] * (n_samples // 2)
        else:
            return self._rule_based_generate(condition, n_samples)
    
    def _rule_based_generate(self, condition: GenerationInput, n_samples: int) -> List[str]:
        candidates = []
        for _ in range(n_samples):
            base = random.choice(KNOWN_CATALYSTS)
            for element, subs in ELEMENT_SUBS.items():
                if random.random() < 0.3 and element in base:
                    new = base.replace(element, random.choice(subs))
                    candidates.append(new)
            if not candidates or random.random() < 0.2:
                candidates.append(base)
        return candidates[:n_samples]

