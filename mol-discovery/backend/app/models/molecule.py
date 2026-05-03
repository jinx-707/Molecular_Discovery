from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal

class MoleculeBase(BaseModel):
    smiles: str = Field(..., description="SMILES string")
    name: Optional[str] = None

class MoleculeCreate(MoleculeBase):
    pass

class Molecule(MoleculeBase):
    id: int
    embedding: List[Decimal] = Field(default_factory=list)
    
    class Config:
        from_attributes = True

