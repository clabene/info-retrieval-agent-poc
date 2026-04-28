# Story 1.3: Provider Factory Functions

Status: review

## Story

As a developer,
I want factory functions that create LLM, embedding, and vector store instances from config,
so that I can swap providers by changing environment variables without code changes.

## Acceptance Criteria

1. `src/config/providers.py` exports `get_llm()`, `get_embed_model()`, and `get_vector_store()` functions
2. `get_llm()` returns a LlamaIndex OpenAI LLM instance configured from settings when LLM_PROVIDER=openai
3. `get_embed_model()` returns an OpenAIEmbedding instance configured from settings when EMBED_PROVIDER=openai
4. `get_vector_store()` returns a QdrantVectorStore with hybrid search enabled, using both sync and async clients
5. All factory functions read configuration from `get_settings()`
6. Provider functions are importable from `src.config` package

## Tasks / Subtasks

- [x] Task 1: Create LLM provider factory (AC: #1, #2, #5)
  - [x] Create `src/config/providers.py`
  - [x] Implement `get_llm()` that reads `settings.llm_provider` and `settings.llm_model`
  - [x] For provider "openai": return `OpenAI(model=settings.llm_model, api_key=settings.openai_api_key)`
  - [x] Import from `llama_index.llms.openai`
- [x] Task 2: Create embedding provider factory (AC: #1, #3, #5)
  - [x] Implement `get_embed_model()` that reads `settings.embed_provider` and `settings.embed_model`
  - [x] For provider "openai": return `OpenAIEmbedding(model=settings.embed_model, api_key=settings.openai_api_key)`
  - [x] Import from `llama_index.embeddings.openai`
- [x] Task 3: Create vector store factory (AC: #1, #4, #5)
  - [x] Implement `get_vector_store()` that creates QdrantVectorStore
  - [x] Create both `QdrantClient` and `AsyncQdrantClient` using `settings.qdrant_host` and `settings.qdrant_port`
  - [x] Return `QdrantVectorStore(collection_name="knowledge_base", client=client, aclient=aclient, enable_hybrid=True, fastembed_sparse_model="Qdrant/bm25")`
  - [x] Import from `llama_index.vector_stores.qdrant` and `qdrant_client`
- [x] Task 4: Export from package (AC: #6)
  - [x] Add `get_llm`, `get_embed_model`, `get_vector_store` to `src/config/__init__.py` exports
- [x] Task 5: Write tests (AC: #1-#6)
  - [x] Create `tests/test_providers.py`
  - [x] Test: `get_llm()` returns an OpenAI LLM instance with correct model
  - [x] Test: `get_embed_model()` returns an OpenAIEmbedding instance with correct model
  - [x] Test: `get_vector_store()` returns a QdrantVectorStore with hybrid enabled
  - [x] Test: all three functions are importable from `src.config`
  - [x] Use mocking/patching to avoid real API calls or Qdrant connections

## Dev Notes

### Architecture Compliance

- File: `src/config/providers.py` [Source: architecture.md#Project Structure & Boundaries]
- Layer: `config/` — imports from third-party only (LlamaIndex, qdrant-client), NOT from `core/` or `api/`
- Factory pattern keyed on env vars [Source: architecture.md#Configuration Management]
- Collection name: `knowledge_base` [Source: architecture.md#Data Architecture]

### Key Technical Details

From architecture [Source: architecture.md#Core Architectural Decisions]:
- Embedding model: `text-embedding-3-small` (1536 dimensions)
- LLM: `gpt-4o-mini` via OpenAI
- Qdrant hybrid search: `enable_hybrid=True`, `fastembed_sparse_model="Qdrant/bm25"`
- Both sync and async Qdrant clients required

### Previous Story Intelligence

From Story 1.2:
- `get_settings()` returns a cached Settings instance with all config values
- Import pattern: `from src.config.settings import get_settings`
- Settings fields: `openai_api_key`, `llm_provider`, `llm_model`, `embed_provider`, `embed_model`, `qdrant_host`, `qdrant_port`

### Testing Approach

Mock the external clients to avoid real connections:

```python
from unittest.mock import patch, MagicMock

@patch("src.config.providers.QdrantClient")
@patch("src.config.providers.AsyncQdrantClient")
def test_get_vector_store(mock_async, mock_sync, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    from src.config.providers import get_vector_store
    vs = get_vector_store()
    assert vs is not None
```

### Anti-Patterns to Avoid

- Do NOT instantiate Settings directly — use `get_settings()` for consistency
- Do NOT cache provider instances with `@lru_cache` — they may need fresh creation per request context
- Do NOT add Ollama/Anthropic provider branches yet — those are Phase 2 (post-MVP)
- Do NOT create the Qdrant collection here — that belongs to Story 2.1

### References

- [Source: architecture.md#Configuration Management]
- [Source: architecture.md#Core Architectural Decisions → Data Architecture]
- [Source: architecture.md#Core Architectural Decisions → API & Communication Patterns]
- [Source: prd.md#FR25 — System supports swapping LLM provider via environment variable]
- [Source: prd.md#FR26 — System supports swapping embedding provider via environment variable]
- [Source: epics.md#Epic 1 → Story 1.3]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4 (via pi coding agent)

### Debug Log References

None — clean implementation.

### Completion Notes List

- `get_llm()`: Returns OpenAI LLM from settings, raises ValueError for unsupported providers
- `get_embed_model()`: Returns OpenAIEmbedding from settings, raises ValueError for unsupported providers
- `get_vector_store()`: Returns QdrantVectorStore with hybrid search (dense + BM25), sync + async clients
- All exported from `src.config` package
- 7 tests covering: correct instances, unsupported providers, custom host/port, package exports
- Full test suite: 14 tests passing, no regressions, ruff clean

### File List

- src/config/providers.py (new)
- src/config/__init__.py (modified — added provider exports)
- tests/test_providers.py (new)

### Change Log

- 2026-04-27: Story 1.3 implemented — provider factory functions with 7 tests passing
