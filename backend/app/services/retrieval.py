from functools import lru_cache
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
from backend.app.config import QDRANT_PATH, COLLECTION, EMBEDDING_MODEL

@lru_cache(maxsize=1)
def embedder():
    return SentenceTransformer(EMBEDDING_MODEL)

@lru_cache(maxsize=1)
def qdrant():
    client = QdrantClient(path=str(QDRANT_PATH))
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
        )
    return client

def index_chunks(document_id: str, filename: str, chunks: list[str]):
    model = embedder()
    vectors = model.encode(chunks, normalize_embeddings=True).tolist()
    points = [
        models.PointStruct(
            id=i,
            vector=vector,
            payload={"document_id": document_id, "filename": filename, "chunk_index": i, "text": chunk}
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]
    # UUID-derived integer IDs avoid collisions between documents.
    import uuid
    points = [
        models.PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document_id}:{i}")),
            vector=vector,
            payload={"document_id": document_id, "filename": filename, "chunk_index": i, "text": chunk}
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors))
    ]
    qdrant().upsert(collection_name=COLLECTION, points=points)
    return len(points)

def search_chunks(query: str, top_k: int = 5, document_id: str | None = None):
    vector = embedder().encode(query, normalize_embeddings=True).tolist()
    query_filter = None
    if document_id:
        query_filter = models.Filter(
            must=[models.FieldCondition(key="document_id", match=models.MatchValue(value=document_id))]
        )
    result = qdrant().query_points(
        collection_name=COLLECTION, query=vector, query_filter=query_filter, limit=top_k
    )
    return [
        {"score": p.score, "text": p.payload.get("text", ""), "document_id": p.payload.get("document_id"),
         "filename": p.payload.get("filename"), "chunk_index": p.payload.get("chunk_index")}
        for p in result.points
    ]
