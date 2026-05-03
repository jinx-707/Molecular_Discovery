from fastapi import APIRouter, Depends
from ...core.auth import require_auth

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("/hypothesis/{discrepancy_id}/accept")
async def accept_hypothesis(discrepancy_id: str, api_key = Depends(require_auth)):
    # Weight feature more in retraining
    print(f"Hypothesis accepted for discrepancy {discrepancy_id}")
    return {"status": "accepted", "next_retrain_weighted": True}

@router.get("/retraining/history")
async def retraining_history(api_key = Depends(require_auth)):
    return [
        {"version": "v1.0", "date": "2024-04-01", "trigger": "manual", "delta_acc": "+0.05"},
        {"version": "v1.1", "date": "2024-04-08", "trigger": "discrepancy", "delta_acc": "+0.03"}
    ]

