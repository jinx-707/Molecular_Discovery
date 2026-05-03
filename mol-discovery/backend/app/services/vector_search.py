from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from typing import List
from ..core.config import settings

client = QdrantClient(settings.QDRANT_URL)

async def index_molecule_embedding(smiles: str, embedding: List[float], payload: dict):
    point = PointStruct(
        id=smiles,
        vector=embedding,
        payload=payload
    )
    client.upsert(
        collection_name="molecules",
        points=[point]
    )

async def search_similar(smiles: str, embedding: List[float], limit: int = 10):
    return client.search(
        collection_name="molecules",
        query_vector=embedding,
        limit=limit
    )

