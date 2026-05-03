from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

log = logging.getLogger(__name__)

app = FastAPI(title="MolDiscovery", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "MolDiscovery API ready"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Health endpoints for demo
@app.post("/api/discovery/start")
async def start_discovery(request: dict):
    reaction = request.get("reaction", "ethanol → jet")
    return {"run_id": f"run_{hash(reaction)}", "status": "running"}

@app.get("/api/discovery/{run_id}/results")
async def get_results(run_id: str):
    return {"run_id": run_id, "candidates": [{"smiles": "TiO2-Ga", "score": 0.92}, {"smiles": "ZSM5", "score": 0.87}] * 10}

print("API endpoints ready")

