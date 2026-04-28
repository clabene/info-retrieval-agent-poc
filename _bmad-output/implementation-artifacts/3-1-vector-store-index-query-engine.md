# Story 3.1: Vector Store Index & Query Engine

Status: ready-for-dev

## Story

As a developer,
I want a VectorStoreIndex over the Qdrant collection with hybrid search configured,
so that the agent has a retrieval tool that combines dense and sparse search.

## Acceptance Criteria

1. A VectorStoreIndex is created from the existing QdrantVectorStore
2. A query engine is configured with similarity_top_k=5, sparse_top_k=12, vector_store_query_mode="hybrid"
3. The query engine is wrapped as a QueryEngineTool with descriptive name and description
4. A function in `src/core/agent.py` returns the configured QueryEngineTool

## Tasks / Subtasks

- [ ] Task 1: Implement query engine tool construction (AC: #1-#4)
  - [ ] Create `src/core/agent.py` with `build_query_engine_tool()` function
  - [ ] Create VectorStoreIndex from get_vector_store()
  - [ ] Configure query engine with hybrid search params
  - [ ] Wrap as QueryEngineTool with name="knowledge_base" and descriptive description
- [ ] Task 2: Write tests (AC: #1-#4)
  - [ ] Test: build_query_engine_tool() returns a QueryEngineTool
  - [ ] Test: tool has correct name "knowledge_base"
  - [ ] Mock vector store to avoid Qdrant dependency

## Dev Notes

### Implementation Pattern

```python
from llama_index.core import VectorStoreIndex
from llama_index.core.tools import QueryEngineTool
from src.config.providers import get_vector_store

def build_query_engine_tool() -> QueryEngineTool:
    vector_store = get_vector_store()
    index = VectorStoreIndex.from_vector_store(vector_store)
    query_engine = index.as_query_engine(
        similarity_top_k=5,
        sparse_top_k=12,
        vector_store_query_mode="hybrid",
    )
    return QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="knowledge_base",
        description="Search the knowledge base for information from ingested documents. Use for any question about indexed content.",
    )
```

### References

- [Source: architecture.md#Core Architectural Decisions → Data Architecture]
- [Source: technical research → Agent + RAG Tool Pattern]
- [Source: epics.md#Epic 3 → Story 3.1]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

### Change Log
