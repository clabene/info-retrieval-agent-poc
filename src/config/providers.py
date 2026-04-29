"""Provider factory functions for LLM, embeddings, and vector store."""

from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import AsyncQdrantClient, QdrantClient

from src.config.settings import get_settings


def get_llm() -> OpenAI:
    """Create LLM instance from settings.

    Supports providers: openai, zen (OpenCode Zen gateway).
    """
    settings = get_settings()
    if settings.llm_provider == "openai":
        return OpenAI(model=settings.llm_model, api_key=settings.openai_api_key)
    if settings.llm_provider == "zen":
        api_base = settings.llm_api_base or "https://opencode.ai/zen/v1"
        api_key = settings.zen_api_key
        if not api_key:
            raise ValueError("ZEN_API_KEY is required when LLM_PROVIDER=zen")
        return OpenAI(model=settings.llm_model, api_key=api_key, api_base=api_base)
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")


def get_embed_model():
    """Create embedding model instance from settings.

    Supports providers: openai, huggingface.
    """
    settings = get_settings()
    if settings.embed_provider == "openai":
        return OpenAIEmbedding(model=settings.embed_model, api_key=settings.openai_api_key)
    if settings.embed_provider == "huggingface":
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding

        return HuggingFaceEmbedding(model_name=settings.embed_model, show_progress_bar=True)
    raise ValueError(f"Unsupported embedding provider: {settings.embed_provider}")


def get_vector_store() -> QdrantVectorStore:
    """Create QdrantVectorStore with hybrid search enabled.

    Creates both sync and async clients for maximum compatibility.
    Does NOT create the collection — that is handled by the ingestion pipeline.
    """
    settings = get_settings()
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    aclient = AsyncQdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    return QdrantVectorStore(
        collection_name="knowledge_base",
        client=client,
        aclient=aclient,
        enable_hybrid=True,
        fastembed_sparse_model="Qdrant/bm25",
        batch_size=20,
    )
