#!/usr/bin/env python3
"""
Download (or stub) pre-trained models for MolDiscovery.

Priority order:
  1. HuggingFace Hub  (if huggingface_hub is installed and repo exists)
  2. JSON demo stubs  (always works — no network required)

Usage:
    python scripts/download_models.py
"""
import json
import sys
from pathlib import Path

# Make sure `app` package is importable when run from the backend dir
sys.path.insert(0, str(Path(__file__).parent.parent))

MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# HuggingFace helper
# ---------------------------------------------------------------------------

def _try_hf_download(repo_id: str, filename: str) -> bool:
    """Return True if the file was downloaded successfully."""
    try:
        from huggingface_hub import hf_hub_download
        print(f"   Downloading {filename} from {repo_id} …")
        path = hf_hub_download(repo_id=repo_id, filename=filename, local_dir=MODEL_DIR)
        print(f"   ✅ Saved to {path}")
        return True
    except ImportError:
        print("   ⚠️  huggingface_hub not installed — skipping HF download")
        return False
    except Exception as exc:
        print(f"   ⚠️  HF download failed: {exc}")
        return False


# ---------------------------------------------------------------------------
# Demo stub creators
# ---------------------------------------------------------------------------

def _stub_catalyst_model(path: Path) -> None:
    path.write_text(json.dumps({
        "version":     "demo_v1",
        "type":        "CatalystGNN",
        "input_dim":   2048,
        "hidden_dim":  512,
        "output_dim":  3,
        "description": "Demo stub — replace with real weights",
    }, indent=2))


def _stub_diffusion_model(path: Path) -> None:
    path.write_text(json.dumps({
        "version":     "demo_v1",
        "type":        "DiffusionGenerator",
        "latent_dim":  256,
        "description": "Demo stub — replace with real weights",
    }, indent=2))


def _stub_enzyme_model(path: Path) -> None:
    path.write_text(json.dumps({
        "version":       "demo_v1",
        "type":          "ESM2",
        "embedding_dim": 1280,
        "layers":        6,
        "description":   "Demo stub — replace with real ESM-2 weights",
    }, indent=2))


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

MODELS = [
    {
        "name":         "catalyst_predictor",
        "path":         MODEL_DIR / "catalyst_gnn.json",
        "hf_repo":      None,   # set to real repo when available
        "hf_file":      None,
        "stub_creator": _stub_catalyst_model,
    },
    {
        "name":         "diffusion_generator",
        "path":         MODEL_DIR / "diffusion.json",
        "hf_repo":      None,
        "hf_file":      None,
        "stub_creator": _stub_diffusion_model,
    },
    {
        "name":         "enzyme_predictor",
        "path":         MODEL_DIR / "enzyme_esm.json",
        "hf_repo":      None,
        "hf_file":      None,
        "stub_creator": _stub_enzyme_model,
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 55)
    print("  MolDiscovery — Model Downloader")
    print("=" * 55)

    for model in MODELS:
        name = model["name"]
        path = model["path"]

        print(f"\n📦 {name}")

        if path.exists():
            print(f"   ✅ Already present: {path.name}")
            continue

        # Try HuggingFace first
        downloaded = False
        if model.get("hf_repo") and model.get("hf_file"):
            downloaded = _try_hf_download(model["hf_repo"], model["hf_file"])

        # Fall back to demo stub
        if not downloaded:
            print(f"   Creating demo stub: {path.name}")
            model["stub_creator"](path)
            print(f"   ✅ Stub created at {path}")

    print("\n" + "=" * 55)
    print(f"  Done. Models directory: {MODEL_DIR}")
    print("=" * 55)


if __name__ == "__main__":
    main()
