# Info Retrieval Agent — Architecture

**Date:** 2026-04-29

## System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│ Docker Compose                                                 │
│                                                                │
│  ┌──────────────────┐       ┌────────────────────────────────┐│
│  │     Qdrant        │       │        App Container           ││
│  │                   │◄─────►│                                ││
│  │  Dense vectors    │       │  ┌─────────────────────────┐  ││
│  │  (cosine, 1536d)  │       │  │   FastAPI + Gradio UI    │  ││
│  │                   │       │  │   POST /query            │  ││
│  │  Sparse vectors   │       │  │   GET  /health           │  ││
│  │  (BM25, fastembed)│       │  │   /chat → Gradio         │  ││
│  │                   │       │  └──────────┬──────────────┘  ││
│  │  Payload indexes  │       │             │                  ││
│  │  (source_type,    │       │  ┌──────────▼──────────────┐  ││
│  │   file_name)      │       │  │   LlamaIndex Agent       │  ││
│  └──────────────────┘       │  │   FunctionAgent           │  ││
│         ▲                    │  │   + QueryEngineTool       │  ││
│         │                    │  └──────────┬──────────────┘  ││
│         │                    │             │                  ││
│         │ ingestion          │  ┌──────────▼──────────────┐  ││
│         │                    │  │   Provider Layer          │  ││
│         │                    │  │   LLM (OpenAI/Zen)        │  ││
│         │                    │  │   Embeddings (OAI/HF)     │  ││
│         │                    │  │   VectorStore (Qdrant)     │  ││
│         │                    │  └─────────────────────────┘  ││
│         │                    └────────────────────────────────┘│
│         │                                                      │
│    ┌────┴──────────────────┐                                  │
│    │  Ingestion Pipeline    │                                  │
│    │  (ingest.py CLI)       │                                  │
│    │  PDF + Web → Chunk     │                                  │
│    │  → Embed → Store       │                                  │
│    └────────────────────────┘                                  │
└────────────────────────────────────────────────────────────────┘
              │
              ▼
     External LLM API (OpenAI / Zen)
```

## Component Architecture

### 1. Configuration Layer (`src/config/`)

| Component | Responsibility |
|-----------|---------------|
| `settings.py` | Pydantic BaseSettings — loads env vars, validates API keys based on provider selection |
| `providers.py` | Factory functions that construct LLM, embedding model, and QdrantVectorStore instances |

**Design decisions:**
- `@lru_cache` on `get_settings()` ensures single config instance
- Validation happens at import time (fail-fast on bad config)
- Provider factories are called at use-site, not cached (allows different lifecycle per component)

### 2. Core Layer (`src/core/`)

#### Agent (`agent.py`)

- Constructs a `FunctionAgent` with `initial_tool_choice="required"` (forces tool use on first turn)
- Wraps `QueryEngineTool` with monkey-patched `call`/`acall` to capture `source_nodes` into a module-level list
- System prompt constrains the agent to ONLY use the knowledge_base tool (no hallucination from general knowledge)

**Query flow:**
1. User question → FunctionAgent
2. Agent formulates search query → `knowledge_base` tool
3. Tool executes hybrid search (dense top-5 + sparse top-12) on Qdrant
4. Source nodes captured as side-effect
5. Agent evaluates results, may reformulate and search again
6. Agent synthesizes final answer

#### Ingestion (`ingestion.py`)

- **PDF loading:** `SimpleDirectoryReader` with `.pdf` filter
- **Web loading:** trafilatura for generic URLs; dedicated Europe PMC / NCBI efetch pathway for PMC articles
- **Pipeline:** `IngestionPipeline` with `SentenceSplitter(chunk_size=512, chunk_overlap=50)` → embedding model → Qdrant vector store

#### Vector Store (`vector_store.py`)

- Creates collection `knowledge_base` with:
  - Dense vectors: configurable dimensions (default 1536), cosine distance
  - Sparse vectors: `text-sparse-new` field for BM25 via fastembed
  - Payload indexes on `source_type` and `file_name` (keyword type)
- Idempotent — skips creation if collection already exists

### 3. API Layer (`src/api/`)

| Component | Responsibility |
|-----------|---------------|
| `app.py` | FastAPI app with async lifespan, routes, Gradio ChatInterface mount |
| `models.py` | Pydantic schemas: `QueryRequest`, `QueryResponse`, `HealthResponse` |

**Lifespan:** Agent is built once at startup (`build_agent()`) and held in module state.

**Endpoints:**
- `POST /query` — accepts `{"question": "..."}`, returns `{"answer": "...", "sources": [...]}`
- `GET /health` — returns `{"status": "healthy"}`
- `/chat` — Gradio ChatInterface (async, shares the same agent instance)
- `/docs` — auto-generated OpenAPI documentation

## Data Flow

### Ingestion Path

```
PDFs (data/pdfs/) ──┐
                    ├──→ load_pdf_documents() / load_web_documents()
URLs (data/urls.txt)┘     │
                          ▼
                    [Document objects with metadata]
                          │
                          ▼
                    SentenceSplitter (512 tokens, 50 overlap)
                          │
                          ▼
                    Embedding model (dense vectors)
                          │
                          ▼
                    QdrantVectorStore (dense + BM25 sparse auto-generated)
```

### Query Path

```
User question
      │
      ▼
FunctionAgent (system prompt: use tool only)
      │
      ▼ (tool call)
QueryEngineTool → VectorStoreIndex.as_query_engine(hybrid)
      │
      ▼
Qdrant hybrid search (similarity_top_k=5, sparse_top_k=12)
      │
      ▼
Source nodes → captured to _last_sources
      │
      ▼
Agent synthesizes answer (may loop for reformulation)
      │
      ▼
QueryResponse {answer, sources}
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| FunctionAgent over ReActAgent | Simpler tool-calling protocol, better with modern LLMs |
| Hybrid search (dense + BM25) | Combines semantic understanding with keyword precision |
| Separate ingestion CLI | Decouples data loading from serving; ingest runs once per data update |
| Module-level `_last_sources` | Simplest approach for PoC; avoids modifying LlamaIndex internals |
| Provider abstraction via factories | Easy swap between OpenAI ↔ Zen and OpenAI ↔ HuggingFace embeddings |
| `initial_tool_choice="required"` | Prevents agent from answering without searching the knowledge base |
| Chunk size 512, overlap 50 | Balanced granularity for retrieval relevance vs. context completeness |

## Concurrency Model

- FastAPI runs async (uvicorn)
- Agent `run()` is awaited per request
- `_last_sources` is a shared mutable list — cleared before each request, read after
- **Not safe for true concurrent requests** (acceptable for PoC scope)

## External Dependencies

| Service | Connection | Purpose |
|---------|-----------|---------|
| Qdrant | `QDRANT_HOST:QDRANT_PORT` (default localhost:6333) | Vector storage and hybrid search |
| OpenAI API | `api.openai.com` or custom `LLM_API_BASE` | LLM inference + embeddings |
| OpenCode Zen | `opencode.ai/zen/v1` | Alternative LLM provider |
| Europe PMC | `ebi.ac.uk/europepmc/` | PMC article full-text retrieval |
| NCBI E-utilities | `eutils.ncbi.nlm.nih.gov` | PMC fallback retrieval |

---

_Generated using BMAD Method `document-project` workflow_
