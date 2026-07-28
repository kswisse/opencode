from qdrant_client import QdrantClient
from qdrant_client.http import models


class VectorDB:
    def __init__(self, host: str, port: int, collection: str, vector_size: int = 1536):
        self.client = QdrantClient(host=host, port=port)
        self.collection = collection
        self.vector_size = vector_size

    async def ensure_collection(self):
        collections = self.client.get_collections().collections
        names = [c.name for c in collections]
        if self.collection not in names:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(
                    size=self.vector_size,
                    distance=models.Distance.COSINE,
                ),
            )

    async def upsert(self, point_id: str, vector: list[float], payload: dict | None = None):
        self.client.upsert(
            collection_name=self.collection,
            points=[models.PointStruct(id=point_id, vector=vector, payload=payload or {})],
        )

    async def search(self, vector: list[float], limit: int = 10) -> list[models.ScoredPoint]:
        return self.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=limit,
        )
