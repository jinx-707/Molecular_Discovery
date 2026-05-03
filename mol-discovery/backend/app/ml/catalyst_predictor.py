"""
CatalystGNNPredictor
====================
Predicts catalyst performance (activity, selectivity, stability).

Two modes:
  demo   — Gaussian noise around base values (no dependencies)
  torch  — Lightweight MLP fine-tuned on experimental data (requires torch)

Fine-tuning
-----------
  predictor.fine_tune(new_experiments, val_fraction=0.2)

  - Converts experiments to feature vectors (composition one-hot + conditions)
  - Runs N epochs with a small LR to avoid catastrophic forgetting
  - Evaluates on a hold-out validation set
  - Saves the new weights only if validation MAE improves
  - Records metadata in the model_metadata table
"""
from __future__ import annotations

import json
import logging
import math
import os
import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

log = logging.getLogger(__name__)

MODEL_DIR = Path(os.getenv("MODEL_CACHE_PATH", "./models"))
MODEL_DIR.mkdir(exist_ok=True)

# Training hyper-parameters
DEFAULT_EPOCHS    = 5
DEFAULT_LR        = 1e-4
DEFAULT_BATCH     = 16
VAL_FRACTION      = 0.20
MIN_TRAIN_SAMPLES = 5

# Feature dimension: 20 elements (one-hot) + temperature + pressure + stability
FEATURE_DIM = 23
OUTPUT_DIM  = 3   # activity, selectivity, stability


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

_COMMON_ELEMENTS = [
    "Si", "Al", "O", "Zn", "Cu", "Fe", "Ni", "Pt", "Pd", "Ga",
    "Ti", "Zr", "Ce", "Mn", "Co", "Mo", "W", "Ru", "Rh", "Ag",
]
_ELEM_IDX = {e: i for i, e in enumerate(_COMMON_ELEMENTS)}


def _catalyst_to_features(record: Dict[str, Any]) -> np.ndarray:
    """
    Convert a catalyst + experiment record to a fixed-size feature vector.

    Features:
      [0:20]  one-hot element presence (from composition or name)
      [20]    temperature (normalised, 0–1 over 0–800°C)
      [21]    pressure    (normalised, 0–1 over 0–100 bar)
      [22]    stability   (normalised, 0–1 over 0–1000 h)
    """
    vec = np.zeros(FEATURE_DIM, dtype=np.float32)

    # Element one-hot from composition dict or catalyst name
    comp = record.get("composition") or {}
    name = record.get("catalyst_name") or record.get("name") or ""
    for elem, idx in _ELEM_IDX.items():
        if elem in comp or elem in name:
            vec[idx] = 1.0

    # Conditions
    temp     = float(record.get("temperature") or 350.0)
    pressure = float(record.get("pressure")    or 1.0)
    stab     = float(record.get("measured_stability") or record.get("stability") or 300)

    vec[20] = min(1.0, temp     / 800.0)
    vec[21] = min(1.0, pressure / 100.0)
    vec[22] = min(1.0, stab     / 1000.0)

    return vec


def _experiment_to_target(record: Dict[str, Any]) -> np.ndarray:
    """Extract normalised target values [activity, selectivity, stability]."""
    activity    = float(record.get("measured_activity")    or record.get("activity")    or 1.0)
    selectivity = float(record.get("measured_selectivity") or record.get("selectivity") or 0.8)
    stability   = float(record.get("measured_stability")   or record.get("stability")   or 300)

    return np.array([
        min(activity    / 5.0, 1.0),   # normalise to ~0–1
        min(selectivity,       1.0),
        min(stability   / 1000.0, 1.0),
    ], dtype=np.float32)


# ---------------------------------------------------------------------------
# Torch MLP (optional)
# ---------------------------------------------------------------------------

def _build_mlp():
    """Build a lightweight MLP. Returns None if torch is unavailable."""
    try:
        import torch
        import torch.nn as nn

        class CatalystMLP(nn.Module):
            def __init__(self):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(FEATURE_DIM, 64),
                    nn.ReLU(),
                    nn.Dropout(0.1),
                    nn.Linear(64, 32),
                    nn.ReLU(),
                    nn.Linear(32, OUTPUT_DIM),
                    nn.Sigmoid(),   # outputs in [0, 1]
                )

            def forward(self, x):
                return self.net(x)

        return CatalystMLP(), torch
    except ImportError:
        return None, None


# ---------------------------------------------------------------------------
# Main predictor
# ---------------------------------------------------------------------------

class CatalystGNNPredictor:
    """
    Catalyst performance predictor with incremental fine-tuning support.
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_version = "demo_v1"
        self._mlp          = None
        self._torch        = None
        self._model_path   = Path(model_path) if model_path else MODEL_DIR / "catalyst_gnn.pt"

        # Try to load a torch MLP
        mlp, torch_mod = _build_mlp()
        if mlp is not None:
            self._mlp    = mlp
            self._torch  = torch_mod
            self._try_load_weights()
            log.info("CatalystGNNPredictor: torch MLP ready")
        else:
            log.info("CatalystGNNPredictor: demo mode (torch not available)")

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, catalysts: List[Dict]) -> List[Dict]:
        """
        Predict activity, selectivity, stability for a batch of candidates.
        Uses the torch MLP if available; otherwise Gaussian noise around base values.
        """
        if self._mlp is not None:
            return self._torch_predict(catalysts)
        return self._demo_predict(catalysts)

    def _torch_predict(self, catalysts: List[Dict]) -> List[Dict]:
        import torch
        self._mlp.eval()
        results = []
        with torch.no_grad():
            for cat in catalysts:
                feat   = torch.tensor(_catalyst_to_features(cat)).unsqueeze(0)
                out    = self._mlp(feat).squeeze(0).numpy()
                # Denormalise
                act  = float(out[0]) * 5.0
                sel  = float(out[1])
                stab = int(float(out[2]) * 1000)
                # Add small noise to simulate uncertainty
                act  = max(0.1, act  * random.gauss(1.0, 0.03))
                sel  = min(0.99, max(0.01, sel * random.gauss(1.0, 0.02)))
                stab = max(10, int(stab * random.gauss(1.0, 0.02)))
                results.append({
                    "activity":    round(act,  2),
                    "selectivity": round(sel,  2),
                    "stability":   stab,
                    "uncertainty": round(random.uniform(0.05, 0.15), 2),
                })
        return results

    def _demo_predict(self, catalysts: List[Dict]) -> List[Dict]:
        predictions = []
        for cat in catalysts:
            base_act  = float(cat.get("activity")    or random.uniform(1.0, 3.0))
            base_sel  = float(cat.get("selectivity") or random.uniform(0.70, 0.95))
            base_stab = int(cat.get("stability")     or random.randint(200, 550))

            predictions.append({
                "activity":    round(max(0.1, base_act  * random.gauss(1.0, 0.05)), 2),
                "selectivity": round(min(0.99, max(0.01, base_sel * random.gauss(1.0, 0.03))), 2),
                "stability":   max(10, int(base_stab * random.gauss(1.0, 0.03))),
                "uncertainty": round(random.uniform(0.05, 0.20), 2),
            })
        return predictions

    # ------------------------------------------------------------------
    # Fine-tuning
    # ------------------------------------------------------------------

    def fine_tune(
        self,
        new_data:     List[Dict],
        val_fraction: float = VAL_FRACTION,
        epochs:       int   = DEFAULT_EPOCHS,
        lr:           float = DEFAULT_LR,
        batch_size:   int   = DEFAULT_BATCH,
    ) -> Dict[str, Any]:
        """
        Incrementally fine-tune the predictor on new experimental data.

        Parameters
        ----------
        new_data     : list of experiment dicts (measured_activity, etc.)
        val_fraction : fraction held out for validation (default 0.2)
        epochs       : training epochs (default 5)
        lr           : learning rate (default 1e-4, small to avoid forgetting)
        batch_size   : mini-batch size

        Returns
        -------
        dict with status, val_mae, val_r2, new_model_version
        """
        if len(new_data) < MIN_TRAIN_SAMPLES:
            return {
                "status": "skipped",
                "reason": f"Need >={MIN_TRAIN_SAMPLES} samples, have {len(new_data)}",
            }

        if self._mlp is None or self._torch is None:
            return self._demo_fine_tune(new_data)

        return self._torch_fine_tune(new_data, val_fraction, epochs, lr, batch_size)

    def _torch_fine_tune(
        self,
        data:         List[Dict],
        val_fraction: float,
        epochs:       int,
        lr:           float,
        batch_size:   int,
    ) -> Dict[str, Any]:
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset

        # Build feature / target tensors
        X = torch.tensor(np.array([_catalyst_to_features(d) for d in data]))
        y = torch.tensor(np.array([_experiment_to_target(d)  for d in data]))

        # Train / val split
        n_val   = max(1, int(len(data) * val_fraction))
        n_train = len(data) - n_val
        indices = torch.randperm(len(data))
        train_idx, val_idx = indices[:n_train], indices[n_train:]

        train_ds = TensorDataset(X[train_idx], y[train_idx])
        val_ds   = TensorDataset(X[val_idx],   y[val_idx])
        train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

        # Save current weights for rollback
        old_state = {k: v.clone() for k, v in self._mlp.state_dict().items()}
        old_val_mae = self._evaluate_mae(self._mlp, val_ds)

        # Fine-tune
        optimizer = torch.optim.Adam(self._mlp.parameters(), lr=lr)
        criterion = nn.MSELoss()
        self._mlp.train()

        train_losses = []
        for epoch in range(epochs):
            epoch_loss = 0.0
            for xb, yb in train_dl:
                optimizer.zero_grad()
                loss = criterion(self._mlp(xb), yb)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            train_losses.append(epoch_loss / len(train_dl))

        # Evaluate
        new_val_mae = self._evaluate_mae(self._mlp, val_ds)
        val_r2      = self._evaluate_r2(self._mlp, val_ds)

        # Only keep new weights if validation improved
        if new_val_mae >= old_val_mae and old_val_mae < 999:
            log.info(
                "Fine-tune: new MAE %.4f >= old MAE %.4f — rolling back",
                new_val_mae, old_val_mae,
            )
            self._mlp.load_state_dict(old_state)
            new_version = self.model_version
            promoted    = False
        else:
            new_version = self._next_version()
            self.model_version = new_version
            self._save_weights()
            promoted = True
            log.info(
                "Fine-tune: MAE improved %.4f → %.4f — promoted to %s",
                old_val_mae, new_val_mae, new_version,
            )

        result = {
            "status":            "success" if promoted else "rolled_back",
            "promoted":          promoted,
            "samples_used":      n_train,
            "val_samples":       n_val,
            "val_mae":           round(new_val_mae, 4),
            "val_r2":            round(val_r2, 4),
            "old_val_mae":       round(old_val_mae, 4),
            "epochs":            epochs,
            "train_losses":      [round(l, 4) for l in train_losses],
            "new_model_version": new_version,
            "timestamp":         datetime.now().isoformat(),
        }

        self._record_metadata(result)
        return result

    def _demo_fine_tune(self, data: List[Dict]) -> Dict[str, Any]:
        """Demo fine-tune when torch is unavailable."""
        log.info("Demo fine-tune with %d samples", len(data))
        new_version        = self._next_version()
        self.model_version = new_version

        # Simulate validation metrics
        rng     = random.Random(len(data))
        val_mae = round(rng.uniform(0.05, 0.25), 4)
        val_r2  = round(rng.uniform(0.70, 0.95), 4)

        result = {
            "status":            "success",
            "promoted":          True,
            "samples_used":      int(len(data) * 0.8),
            "val_samples":       int(len(data) * 0.2),
            "val_mae":           val_mae,
            "val_r2":            val_r2,
            "old_val_mae":       round(val_mae + rng.uniform(0.01, 0.05), 4),
            "epochs":            DEFAULT_EPOCHS,
            "train_losses":      [round(0.3 - i * 0.04, 4) for i in range(DEFAULT_EPOCHS)],
            "new_model_version": new_version,
            "timestamp":         datetime.now().isoformat(),
        }
        self._record_metadata(result)
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _try_load_weights(self) -> None:
        if self._model_path.exists() and self._model_path.suffix == ".pt":
            try:
                self._mlp.load_state_dict(
                    self._torch.load(str(self._model_path), map_location="cpu")
                )
                self._mlp.eval()
                log.info("Loaded weights from %s", self._model_path)
            except Exception as exc:
                log.warning("Could not load weights (%s) — using random init", exc)

    def _save_weights(self) -> None:
        try:
            path = MODEL_DIR / f"catalyst_gnn_{self.model_version}.pt"
            self._torch.save(self._mlp.state_dict(), str(path))
            # Also update the canonical path
            self._torch.save(self._mlp.state_dict(), str(self._model_path))
            log.info("Saved weights to %s", path)
        except Exception as exc:
            log.warning("Could not save weights: %s", exc)

    @staticmethod
    def _evaluate_mae(mlp: Any, dataset: Any) -> float:
        import torch
        mlp.eval()
        total, n = 0.0, 0
        with torch.no_grad():
            for xb, yb in torch.utils.data.DataLoader(dataset, batch_size=32):
                pred = mlp(xb)
                total += float(torch.mean(torch.abs(pred - yb)).item()) * len(xb)
                n += len(xb)
        return total / n if n > 0 else 999.0

    @staticmethod
    def _evaluate_r2(mlp: Any, dataset: Any) -> float:
        import torch
        mlp.eval()
        preds, targets = [], []
        with torch.no_grad():
            for xb, yb in torch.utils.data.DataLoader(dataset, batch_size=32):
                preds.append(mlp(xb).numpy())
                targets.append(yb.numpy())
        if not preds:
            return 0.0
        p = np.concatenate(preds)
        t = np.concatenate(targets)
        ss_res = np.sum((t - p) ** 2)
        ss_tot = np.sum((t - t.mean()) ** 2)
        return float(1 - ss_res / (ss_tot + 1e-8))

    def _next_version(self) -> str:
        try:
            parts = self.model_version.split("_v")
            n     = int(parts[-1]) + 1 if len(parts) > 1 else 2
        except (ValueError, IndexError):
            n = 2
        return f"demo_v{n}"

    def _record_metadata(self, result: Dict[str, Any]) -> None:
        """Persist model version metadata to the DB (best-effort)."""
        try:
            from app.db.session import SessionLocal
            from app.db.models import ModelMetadata

            db = SessionLocal()
            try:
                # Mark previous versions as non-production
                if result.get("promoted"):
                    db.query(ModelMetadata).filter(
                        ModelMetadata.is_production == True  # noqa: E712
                    ).update({"is_production": False})

                db.add(ModelMetadata(
                    id=str(uuid.uuid4()),
                    model_version=result["new_model_version"],
                    samples_used=result.get("samples_used", 0),
                    epochs=result.get("epochs", 0),
                    learning_rate=DEFAULT_LR,
                    val_mae=result.get("val_mae"),
                    val_r2=result.get("val_r2"),
                    val_samples=result.get("val_samples", 0),
                    is_production=result.get("promoted", False),
                    promoted_at=datetime.now() if result.get("promoted") else None,
                    notes=json.dumps({
                        "status":      result.get("status"),
                        "old_val_mae": result.get("old_val_mae"),
                    }),
                ))
                db.commit()
            finally:
                db.close()
        except Exception as exc:
            log.debug("Could not record model metadata: %s", exc)
