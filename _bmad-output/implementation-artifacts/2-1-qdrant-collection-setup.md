# Story 2.1: Qdrant Collection Setup

Status: ready-for-dev

## Story

As a developer,
I want the Qdrant collection created with proper vector configuration and payload indexes,
so that ingested documents are stored optimally for hybrid search.

## Acceptance Criteria

1. A function in `src/core/vector_store.py` creates the `knowledge_base` collection
2. Collection has dense vectors (1536 dims, cosine distance) and sparse vector config for BM25
3. Payload indexes are created for `source_type` (keyword) and `file_name` (keyword)
4. If the collection already exists, it is not recreated or overwritten
5. Function uses settings from `src/config` for Qdrant connection

## Tasks / Subtasks

- [ ] Task 1: Implement collection setup function (AC: #1, #2, #3, #4, #5)
  - [ ] Create `src/core/vector_store.py` with `ensure_collection()` function
  - [ ] Check if collection exists first (`client.collection_exists()`)
  - [ ] If not exists: create collection with `VectorParams(size=1536, distance=Distance.COSINE)` and `SparseVectorParams` for BM25
  - [ ] Create payload indexes for `source_type` and `file_name` (keyword type)
  - [ ] Use `QdrantClient` from settings (host/port) — NOT from providers.get_vector_store() which is for LlamaIndex
- [ ] Task 2: Write tests (AC: #1-#5)
  - [ ] Create `tests/test_vector_store.py`
  - [ ] Test: collection is created when it doesn't exist (mock client)
  - [ ] Test: collection is NOT recreated when it already exists
  - [ ] Test: payload indexes are created after collection creation
  - [ ] Test: correct vector params (1536, cosine) and sparse config

## Dev Notes

### Architecture Compliance

- File: `src/core/vector_store.py` [Source: architecture.md#Project Structure & Boundaries]
- Layer: `core/` — imports from `config/` only [Source: architecture.md#Implementation Patterns]
- Collection name: `knowledge_base` [Source: architecture.md#Data Architecture]
- Distance: Cosine [Source: architecture.md#Core Architectural Decisions → Data Architecture]
- Payload indexes: `source_type` (keyword), `file_name` (keyword) — created at init [Source: architecture.md#Data Architecture]

### Key Technical Details

From research [Source: technical research]:
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, SparseVectorParams

client.create_collection(
    collection_name="knowledge_base",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    sparse_vectors_config={"text": SparseVectorParams()},
)
```

Note: The sparse vector field name "text" is what LlamaIndex's QdrantVectorStore uses internally when `enable_hybrid=True`.

### Important: Sync Client for Setup

Use a direct `QdrantClient` for collection setup (not the LlamaIndex QdrantVectorStore wrapper). The setup is a one-time admin operation, not a query-time operation.

```python
from src.config.settings import get_settings

def ensure_collection() -> None:
    settings = get_settings()
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    # ... setup logic
```

### Previous Story Intelligence

From Story 1.3:
- `get_settings()` provides `qdrant_host` and `qdrant_port`
- `get_vector_store()` in providers.py creates the LlamaIndex QdrantVectorStore (used at query time, not setup time)
- Settings cache works via `@lru_cache`

### Anti-Patterns to Avoid

- Do NOT use `get_vector_store()` from providers — that's the LlamaIndex wrapper for query time
- Do NOT delete/recreate existing collections — idempotent setup only
- Do NOT add ingestion logic here — that belongs to Stories 2.2-2.5
- Do NOT create indexes before the collection exists

### References

- [Source: architecture.md#Core Architectural Decisions → Data Architecture]
- [Source: technical research → Qdrant Collection Setup for Our Stack]
- [Source: technical research → Payload Indexing for Metadata Filtering]
- [Source: epics.md#Epic 2 → Story 2.1]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

### Change Log
