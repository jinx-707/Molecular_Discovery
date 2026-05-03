import torch
import torch.nn.functional as F
from typing import List, Dict
from .base import Prediction

def monte_carlo_dropout(model: torch.nn.Module, inputs: torch.Tensor, n_samples: int = 10) -> torch.Tensor:
    """MC Dropout uncertainty for any model"""
    model.train()  # Enable dropout
    preds = []
    with torch.no_grad():
        for _ in range(n_samples):
            pred = model(inputs)
            preds.append(pred)
    preds = torch.stack(preds)
    mean = preds.mean(0)
    std = preds.std(0)
    return mean, std

def ensemble_uncertainty(models: List[torch.nn.Module], inputs: torch.Tensor) -> torch.Tensor:
    """Ensemble variance"""
    preds = [model(inputs) for model in models]
    preds = torch.stack(preds)
    return preds.mean(0), preds.std(0)

def prediction_with_uncertainty(mean: torch.Tensor, std: torch.Tensor) -> Prediction:
    return Prediction(
        activity=float(mean[0]),
        selectivity=float(mean[1]),
        stability=float(mean[2]),
        uncertainty=float(std.mean())
    )

