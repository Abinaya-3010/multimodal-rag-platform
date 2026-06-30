from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
from app.core.config import get_settings

settings = get_settings()

# Single shared Qdrant client instance for the whole application
# Created once, reused everywhere — connection pooling is handled internally
qdrant = QdrantClient(
    host=settings.qdrant_host,
    port=settings.qdrant_port,
)


def create_tenant_collection(collection_name: str) -> None:
    """
    Creates a new Qdrant collection for a tenant.

    vector size 1536 matches OpenAI's text-embedding-3-small model.
    distance Cosine is the standard similarity metric for text embeddings —
    it measures the angle between vectors, ignoring magnitude.

    If the collection already exists, Qdrant raises an exception.
    We let that propagate so the saga can detect the failure.
    """
    qdrant.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=1536,
            distance=Distance.COSINE,
        ),
    )


def delete_tenant_collection(collection_name: str) -> None:
    """
    Deletes a tenant's collection entirely.
    Used both for rollback (if provisioning fails partway)
    and for tenant offboarding (GDPR deletion requests).
    """
    qdrant.delete_collection(collection_name=collection_name)


def collection_exists(collection_name: str) -> bool:
    """
    Checks if a collection already exists.
    Used to verify provisioning succeeded.
    """
    collections = qdrant.get_collections().collections
    return any(c.name == collection_name for c in collections)