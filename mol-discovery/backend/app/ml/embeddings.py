import torch
from sentence_transformers import SentenceTransformer
from rdkit import Chem
from rdkit.Chem import AllChem

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def smiles_to_embedding(smiles: str) -> torch.Tensor:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("Invalid SMILES")
    
    # Generate fingerprint
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
    
    # Convert to embedding
    fp_array = torch.tensor(fp.ToBitString(), dtype=torch.float32)
    return model.encode([smiles])[0]  # Chemical + text embedding

