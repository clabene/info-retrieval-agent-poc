"""Qdrant collection setup and management."""

import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, SparseVectorParams, VectorParams

from src.config.settings import get_settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "knowledge_base"


def ensure_collection() -> None:
    """Create the knowledge_base collection if it doesn't exist.

    Sets up:
    - Dense vectors: 1536 dimensions, cosine distance (for text-embedding-3-small)
    - Sparse vectors: BM25 via fastembed (field name "text" for LlamaIndex compatibility)
    - Payload indexes: source_type (keyword), file_name (keyword)

    Idempotent — safe to call multiple times.
    """
    settings = get_settings()
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    if client.collection_exists(COLLECTION_NAME):
        logger.info("Collection '%s' already exists — skipping creation.", COLLECTION_NAME)
        return

    logger.info("Creating collection '%s' (dims=%d)...", COLLECTION_NAME, settings.embed_dims)
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=settings.embed_dims, distance=Distance.COSINE),
        sparse_vectors_config={"text-sparse-new": SparseVectorParams()},
    )

    # Create payload indexes for efficient metadata filtering
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="source_type",
        field_schema="keyword",
    )
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="file_name",
        field_schema="keyword",
    )

    logger.info("Collection '%s' created with payload indexes.", COLLECTION_NAME)
