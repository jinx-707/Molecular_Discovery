from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union, Tuple
import torch
from pydantic import BaseModel

class Prediction(BaseModel):
    activity: float  # mol/g/h for catalysts, relative activity for enzymes
    selectivity: float  # 0-1
    stability: float  # hours
    uncertainty: float  # std dev

class GenerationInput(BaseModel):
    condition: str  # reaction SMILES or substrate
    constraints: Dict[str, Any] = {}

class ModelInput(BaseModel):
    smiles: str  # or sequence for enzymes
    metadata: Dict[str, Any] = {}

class Predictor(ABC):
    @abstractmethod
    def predict(self, candidates: List[ModelInput]) -> List[Prediction]:
        """Predict properties for batch of candidates"""
        pass
    
    @abstractmethod
    def fine_tune(self, data: List[Tuple[ModelInput, Dict[str, float]]]) -> None:
        """Fine-tune on labeled data (stub)"""
        pass

class Generator(ABC):
    @abstractmethod
    def generate(self, condition: GenerationInput, n_samples: int = 10) -> List[str]:
        """Generate novel candidates given condition"""
        pass

