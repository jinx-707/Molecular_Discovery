#!/usr/bin/env python3
import os
from pathlib import Path
import urllib.request

MODELS_DIR = Path("backend/models/sim")
MODELS_DIR.mkdir(exist_ok=True, parents=True)

def download_model(url: str, filename: str):
    path = MODELS_DIR / filename
    if not path.exists():
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, str(path))
    print(f"{filename}: OK")

if __name__ == "__main__":
    # SchNet for reaction energies
    download_model(
        "https://github.com/atomistic-machine-learning/schnetpack/raw/master/tests/data/schnet_ethanol.pt",
        "schnet_reaction.pt"
    )
    
    # Cobrapy models
    cobrapy_dir = MODELS_DIR / "cobrapy"
    cobrapy_dir.mkdir(exist_ok=True)
    
    print("Download cobrapy models manually:")
    print("wget https://bigg.ucsd.edu/static/models/iJO1366.xml -O backend/models/sim/cobrapy/iJO1366.xml")
    print("Models ready (or use stubs)!")

