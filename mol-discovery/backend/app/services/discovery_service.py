import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models import Catalyst, DiscoveryRun, Prediction
from app.ml.catalyst_predictor import CatalystGNNPredictor
from app.ml.catalyst_generator import CatalystDiffusionGenerator
from app.data.ingestor import DataIngestor

class DiscoveryService:
    def __init__(self):
        self.predictor = CatalystGNNPredictor()
        self.generator = CatalystDiffusionGenerator()
        self.ingestor = DataIngestor()
    
    async def run_discovery(
        self, 
        reaction: str, 
        constraints: dict = None, 
        user_id: str = "demo_user"
    ) -> Dict[str, Any]:
        """Run discovery workflow - FIXED: Creates DB records before predictions"""
        db = SessionLocal()
        
        try:
            run_id = str(uuid.uuid4())
            
            # Create discovery run record
            discovery_run = DiscoveryRun(
                id=run_id,
                user_id=user_id,
                target_reaction=reaction,
                constraints=constraints or {},
                status="running",
            )
            db.add(discovery_run)
            db.commit()
            
            # Get known catalysts from database
            known_catalysts = db.query(Catalyst).filter(
                Catalyst.reaction_target.ilike(f"%{reaction}%")
            ).limit(10).all()
            
            candidates = []
            
            # Add known catalysts (already have IDs in DB)
            for cat in known_catalysts:
                candidates.append({
                    "id": cat.id,
                    "name": cat.name,
                    "type": "known",
                    "predicted_activity": cat.reported_activity or 1.5,
                    "predicted_selectivity": cat.reported_selectivity or 0.8,
                    "predicted_stability": cat.reported_stability or 300,
                    "uncertainty": 0.10,
                    "score": round((cat.reported_activity or 1.5) / 3.5 * 0.4 + (cat.reported_selectivity or 0.8) * 0.3, 3)
                })
            
            # Generate novel catalysts and INSERT them into database FIRST
            novel_templates = [
                {"name": "ZSM-5 with Ga substitution", "activity": 2.4, "selectivity": 0.88, "stability": 520},
                {"name": "SAPO-34 with Ni clusters", "activity": 2.1, "selectivity": 0.85, "stability": 480},
                {"name": "Phosphotungstic acid on HY", "activity": 1.9, "selectivity": 0.83, "stability": 420},
                {"name": "Mesoporous ZSM-5", "activity": 2.0, "selectivity": 0.84, "stability": 450},
                {"name": "Beta zeolite with Ti", "activity": 1.7, "selectivity": 0.79, "stability": 380},
            ]
            
            for template in novel_templates:
                # Create catalyst record in database FIRST
                new_catalyst = Catalyst(
                    id=str(uuid.uuid4()),
                    name=template["name"],
                    composition={"type": "novel_generated"},
                    catalyst_type="generated",
                    reaction_target=reaction,
                    source="ai_generated",
                )
                db.add(new_catalyst)
                db.flush()  # This assigns the ID
                
                # Now add to candidates with the REAL database ID
                candidates.append({
                    "id": new_catalyst.id,  # Use REAL DB ID, not "syn_0"
                    "name": template["name"],
                    "type": "novel",
                    "predicted_activity": template["activity"],
                    "predicted_selectivity": template["selectivity"],
                    "predicted_stability": template["stability"],
                    "uncertainty": 0.15,
                    "score": round(template["activity"] / 3.5 * 0.4 + template["selectivity"] * 0.3, 3)
                })
            
            # Now store predictions - all candidate IDs now exist in catalysts table
            for candidate in candidates:
                prediction = Prediction(
                    id=str(uuid.uuid4()),
                    candidate_id=candidate["id"],
                    model_version="demo_v1",
                    predicted_activity=candidate["predicted_activity"],
                    predicted_selectivity=candidate["predicted_selectivity"],
                    predicted_stability=candidate["predicted_stability"],
                    uncertainty=candidate["uncertainty"],
                )
                db.add(prediction)
            
            # Sort candidates by score
            candidates.sort(key=lambda x: x["score"], reverse=True)
            
            # Update discovery run
            discovery_run.status = "completed"
            discovery_run.known_count = len(known_catalysts)
            discovery_run.novel_count = len(novel_templates)
            discovery_run.completed_at = datetime.now()
            db.commit()
            
            return {
                "run_id": run_id,
                "status": "completed",
                "total_candidates": len(candidates),
                "known_count": len(known_catalysts),
                "novel_count": len(novel_templates),
                "candidates": candidates[:20]
            }
            
        except Exception as e:
            db.rollback()
            print(f"Error in discovery: {e}")
            import traceback
            traceback.print_exc()
            raise e
        finally:
            db.close()
    
    def get_results(self, run_id: str) -> Dict[str, Any]:
        """Retrieve discovery results from database"""
        db = SessionLocal()
        try:
            discovery_run = db.query(DiscoveryRun).filter(DiscoveryRun.id == run_id).first()
            if not discovery_run:
                return {"error": "Run not found"}
            
            predictions = db.query(Prediction).join(
                Catalyst, Prediction.candidate_id == Catalyst.id
            ).filter(
                Prediction.candidate_id.in_(
                    db.query(Prediction.candidate_id)
                )
            ).all()
            
            return {
                "run_id": discovery_run.id,
                "target_reaction": discovery_run.target_reaction,
                "status": discovery_run.status,
                "created_at": discovery_run.created_at.isoformat(),
                "completed_at": discovery_run.completed_at.isoformat() if discovery_run.completed_at else None
            }
        finally:
            db.close()
    
    def get_run_status(self, run_id: str) -> Dict[str, Any]:
        """Get status of a discovery run"""
        db = SessionLocal()
        try:
            run = db.query(DiscoveryRun).filter(DiscoveryRun.id == run_id).first()
            if not run:
                return {"error": "Run not found"}
            return {
                "run_id": run.id,
                "status": run.status,
                "created_at": run.created_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None
            }
        finally:
            db.close()
