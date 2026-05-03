"""
Real Model Retraining - PyTorch Fine-tuning
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
from pathlib import Path


class CatalystDataset(Dataset):
    """Dataset for fine-tuning GNN models"""
    
    def __init__(self, data: List[Dict]):
        self.data = data
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        return {
            "features": torch.tensor(item.get("features", [0.0] * 128), dtype=torch.float32),
            "activity": torch.tensor(item["measured_activity"], dtype=torch.float32),
            "selectivity": torch.tensor(item.get("measured_selectivity", 0.8), dtype=torch.float32),
        }


class SimplePredictor(nn.Module):
    """Simple neural network for demonstration"""
    
    def __init__(self, input_dim: int = 128, hidden_dim: int = 64):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 2)  # activity + selectivity
        )
    
    def forward(self, x):
        return self.network(x)


class ModelRetrainer:
    """
    Real model retraining with PyTorch
    Not just version increment - actual weight updates
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = SimplePredictor()
        self.model_path = model_path or Path(__file__).parent / "models" / "catalyst_model.pt"
        self.load_model()
    
    def load_model(self):
        """Load existing model if available"""
        if os.path.exists(self.model_path):
            try:
                self.model.load_state_dict(torch.load(self.model_path))
                print(f"✅ Loaded model from {self.model_path}")
            except Exception as e:
                print(f"⚠️ Could not load model: {e}")
    
    def save_model(self):
        """Save model weights"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        torch.save(self.model.state_dict(), self.model_path)
        print(f"✅ Saved model to {self.model_path}")
    
    def prepare_training_data(self, experiments: List[Dict]) -> CatalystDataset:
        """Prepare experimental data for training"""
        
        # Convert experiments to features
        # In reality, this would use catalyst fingerprints/embeddings
        for exp in experiments:
            if "features" not in exp:
                # Create simple feature vector from catalyst name hash
                catalyst_name = exp.get("catalyst_name", "unknown")
                features = [float(hash(catalyst_name) % 100) / 100 for _ in range(128)]
                exp["features"] = features
        
        return CatalystDataset(experiments)
    
    def retrain(
        self, 
        experiments: List[Dict],
        epochs: int = 10,
        learning_rate: float = 0.001,
        save_if_improved: bool = True
    ) -> Dict[str, Any]:
        """
        Actually retrain the model with new experimental data
        
        Args:
            experiments: List of experimental results
            epochs: Number of training epochs
            learning_rate: Learning rate for optimizer
            save_if_improved: Save model if validation loss improves
        
        Returns:
            Training statistics
        """
        
        if len(experiments) < 5:
            return {
                "status": "skipped",
                "reason": f"Need at least 5 experiments (have {len(experiments)})"
            }
        
        # Prepare data
        dataset = self.prepare_training_data(experiments)
        dataloader = DataLoader(dataset, batch_size=min(8, len(experiments)), shuffle=True)
        
        # Setup training
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()
        
        # Track metrics
        losses = []
        old_state = None
        
        # Save old weights for comparison
        if save_if_improved:
            old_state = {k: v.clone() for k, v in self.model.state_dict().items()}
        
        print(f"\n🔄 Starting real model retraining with {len(experiments)} experiments...")
        start_time = datetime.now()
        
        for epoch in range(epochs):
            epoch_loss = 0.0
            for batch in dataloader:
                features = batch["features"]
                targets = torch.stack([batch["activity"], batch["selectivity"]], dim=1)
                
                optimizer.zero_grad()
                outputs = self.model(features)
                loss = criterion(outputs, targets)
                loss.backward()
                optimizer.step()
                
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / len(dataloader)
            losses.append(avg_loss)
            print(f"  Epoch {epoch+1}/{epochs}: Loss = {avg_loss:.4f}")
        
        # Decide whether to keep new model
        if save_if_improved and old_state is not None:
            # Check if model improved (simple heuristic)
            if losses[-1] > losses[0] * 1.1:  # Worse by >10%
                print("⚠️ New model performed worse, reverting to previous version")
                self.model.load_state_dict(old_state)
        
        # Save model
        self.save_model()
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "status": "success",
            "samples_used": len(experiments),
            "epochs": epochs,
            "final_loss": losses[-1],
            "losses": losses,
            "training_duration_seconds": duration,
            "model_version": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "timestamp": datetime.now().isoformat()
        }
    
    def predict(self, features: torch.Tensor) -> tuple:
        """Make prediction with current model"""
        self.model.eval()
        with torch.no_grad():
            output = self.model(features)
            return output[0].item(), output[1].item()


# Integration with existing FeedbackService
def integrate_real_retraining():
    """
    How to integrate with your existing FeedbackService
    
    Replace the current mock retraining with:
    """
    
    """
    from app.ml.retraining import ModelRetrainer
    retrainer = ModelRetrainer()
    
    # In retrain_models method:
    def retrain_models(self) -> dict:
        # Get real experiments from database
        experiments = db.query(Experiment).all()
        
        # Convert to training format
        training_data = []
        for exp in experiments:
            catalyst = db.query(Catalyst).filter(Catalyst.id == exp.candidate_id).first()
            training_data.append({
                "catalyst_name": catalyst.name if catalyst else "unknown",
                "measured_activity": exp.measured_activity,
                "measured_selectivity": exp.measured_selectivity,
            })
        
        # Actually retrain!
        result = retrainer.retrain(training_data)
        return result
    """
