---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
status: 'complete'
completedAt: '2026-04-27'
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/research/technical-llamaindex-agentic-patterns-research-2026-04-22.md'
  - '_bmad-output/brainstorming/brainstorming-session-2026-04-15-1730.md'
workflowType: 'architecture'
project_name: 'info-retrieval-agent'
user_name: 'clabene'
date: '2026-04-27'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
26 FRs across 6 capability areas. The system is a straightforward agentic RAG pipeline with two entry points (CLI for ingestion, HTTP for queries) and a single external dependency (OpenAI API). No multi-user concerns, no auth, no complex state management.

**Non-Functional Requirements:**
- Performance: 60s query timeout, 5min ingestion for 10 docs, 30s startup
- Integration: OpenAI API + local Qdrant only
- Maintainability: 3-layer code structure, pinned dependencies, documented env vars

**Scale & Complexity:**
- Primary domain: Python async API backend
- Complexity level: Low
- Estimated architectural components: 5 (config, ingestion, agent/retrieval, API, containerization)

### Technical Constraints & Dependencies

- OpenAI API required for all LLM and embedding operations (no offline fallback in MVP)
- Embedding model lock-in: switching invalidates all stored vectors, requires full re-ingestion
- Qdrant must be reachable before app serves queries (startup dependency)
- Single process / single container for app (no horizontal scaling needed)
- Python ≥3.10 required by LlamaIndex

### Cross-Cutting Concerns

- **Configuration management:** Env vars drive provider selection, API keys, Qdrant connection
- **Error handling:** Graceful degradation across all layers (ingestion continues on single-file failure, agent admits ignorance, API returns clear error codes)
- **Logging/Observability:** Agent tool calls must be observable in logs (success criterion: ≥2 tool calls visible)
- **Async consistency:** All runtime components (FastAPI, LlamaIndex agent, Qdrant client) must use async patterns

## Starter Template & Project Foundation

### Primary Technology Domain

Python async API backend — LlamaIndex + FastAPI + Qdrant + Gradio.

### Starter Template Decision

**Decision:** No external starter template. Manual project scaffolding.

**Rationale:** The Python AI/RAG ecosystem has no opinionated scaffolding tools equivalent to `create-next-app` or `create-t3-app`. The project structure is simple enough (3 layers, ~8 source files) that manual setup is faster than adapting a generic Python template.

### Project Initialization

```bash
mkdir info-retrieval-agent && cd info-retrieval-agent
uv init  # or: poetry init
```

### Architectural Decisions Established by Foundation

| Decision | Choice |
|----------|--------|
| **Language** | Python ≥3.10 |
| **Package manager** | uv (or pip/poetry) |
| **Project metadata** | `pyproject.toml` (PEP 621) |
| **Code structure** | 3-layer: `src/config/`, `src/core/`, `src/api/` |
| **Entry points** | `main.py` (server), `ingest.py` (CLI) |
| **Dependency management** | Pinned in `pyproject.toml` with lock file |
| **Environment config** | `.env` file loaded by `python-dotenv` / `pydantic-settings` |
| **Containerization** | `Dockerfile` + `docker-compose.yml` |

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
All critical decisions are made — stack is fully defined.

**Deferred Decisions (Post-MVP):**
- Streaming architecture (Phase 2)
- Ollama/Anthropic provider integration details (Phase 2)
- OpenTelemetry instrumentation (Phase 2)
- Cloud deployment target (Phase 3)

### Data Architecture

| Decision | Choice | Rationale |
|----------|--------|----------|
| Vector DB | Qdrant (Docker, persistent volume) | First-class LlamaIndex integration, hybrid search support |
| Embedding model | `text-embedding-3-small` (1536 dims) | Cost-effective, shared API key with LLM |
| Distance metric | Cosine | Standard for OpenAI embeddings; Qdrant normalizes internally |
| Chunking | `SentenceSplitter(chunk_size=512, chunk_overlap=50)` | Balanced precision vs. context; LlamaIndex recommended default |
| Hybrid search | Dense + BM25 sparse via `fastembed` | Low-cost local BM25, improves keyword-specific queries |
| Fusion strategy | Reciprocal Rank Fusion (RRF) | Qdrant built-in, rank-based (no score calibration needed) |
| Retrieval params | `similarity_top_k=5`, `sparse_top_k=12` | 12 candidates per space, fused to top 5 |
| Payload indexes | `source_type` (keyword), `file_name` (keyword) | Created at collection init; enables future metadata filtering |
| PDF parsing | pypdf (default `PDFReader`) | MIT license, adequate for PoC; upgrade path to `unstructured` |
| Web parsing | Direct `trafilatura` | Apache 2.0, avoids GPL `llama-index-readers-web` wrapper |

### Authentication & Security

| Decision | Choice | Rationale |
|----------|--------|----------|
| API authentication | None | Local-only PoC, single user |
| API key handling | `OPENAI_API_KEY` in `.env`, never committed | Standard secret management |
| Network exposure | `localhost` only (Docker port mapping) | No public exposure |

### API & Communication Patterns

| Decision | Choice | Rationale |
|----------|--------|----------|
| API framework | FastAPI (async) | Native async, Pydantic integration, auto OpenAPI docs |
| Request/response validation | Pydantic models | Type-safe, auto-documented |
| Error handling | FastAPI HTTPException (422/500) | Framework default, clear error messages |
| Agent invocation | `await agent.run(user_msg=...)` | LlamaIndex async-first API |
| Gradio mounting | `gr.mount_gradio_app(app, demo, path="/chat")` | Single process, single port, no CORS |

### Configuration Management

| Decision | Choice | Rationale |
|----------|--------|----------|
| Settings library | `pydantic-settings` | Typed, validated, `.env` support built-in |
| Provider switching | Factory functions (`get_llm()`, `get_embed_model()`) keyed on env vars | Clean abstraction, no code changes to swap |
| Required vars | `OPENAI_API_KEY` | Validated at startup; fail fast if missing |
| Optional vars | `LLM_PROVIDER`, `LLM_MODEL`, `EMBED_PROVIDER`, `EMBED_MODEL`, `QDRANT_HOST`, `QDRANT_PORT` | All have sensible defaults |

### Infrastructure & Deployment

| Decision | Choice | Rationale |
|----------|--------|----------|
| Package manager | `uv` | Fastest resolver, modern, PEP 621 native |
| Python version | 3.12 | Current stable, required by nothing older |
| Base Docker image | `python:3.12-slim` | Small footprint, official |
| Linting/formatting | `ruff` | Fast, replaces flake8+black+isort in one tool |
| Container orchestration | Docker Compose v2 | 2 services (qdrant + app), named volume |
| Qdrant image | `qdrant/qdrant:latest` | Official, pinned at deploy time |
| App server | `uvicorn` (single worker) | Async, sufficient for single-user PoC |

### Decision Impact Analysis

**Implementation Sequence:**
1. Project scaffolding (`uv init`, `pyproject.toml`, directory structure)
2. Configuration layer (`pydantic-settings`, provider factories)
3. Vector store setup (Qdrant client, collection creation with indexes)
4. Ingestion pipeline (loaders → SentenceSplitter → embeddings → Qdrant)
5. Agent + QueryEngineTool (FunctionAgent over VectorStoreIndex)
6. API layer (FastAPI endpoints + Gradio mount)
7. Docker Compose packaging

**Cross-Component Dependencies:**
- Config layer is consumed by all other layers (must be built first)
- Vector store setup is shared between ingestion and agent (single `QdrantVectorStore` instance config)
- Agent depends on vector store index existing (ingestion must run before queries work)
- API layer depends on agent being constructable (but not on data being ingested)

## Implementation Patterns & Consistency Rules

### Naming Patterns

**Python Code:**
- Functions/variables: `snake_case` (PEP 8)
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Files/modules: `snake_case.py`
- Private: prefix with `_` (single underscore)

**Qdrant:**
- Collection name: `knowledge_base`
- Payload fields: `snake_case` (`source_type`, `file_name`, `source_url`)

**API:**
- Endpoints: lowercase with slashes (`/query`, `/health`)
- JSON fields: `snake_case` (`source_type`, not `sourceType`)
- Environment variables: `UPPER_SNAKE_CASE` (`OPENAI_API_KEY`, `QDRANT_HOST`)

### Structure Patterns

**Module organization:**
```
src/
├── config/          # Settings, provider factories — no business logic
│   ├── __init__.py
│   ├── settings.py  # Pydantic Settings class
│   └── providers.py # get_llm(), get_embed_model(), get_vector_store()
├── core/            # Business logic — no HTTP/API concerns
│   ├── __init__.py
│   ├── ingestion.py # IngestionPipeline setup and execution
│   ├── agent.py     # FunctionAgent construction and QueryEngineTool
│   └── vector_store.py # Qdrant client, collection setup, index creation
└── api/             # HTTP layer — no direct LlamaIndex imports
    ├── __init__.py
    ├── app.py       # FastAPI app, route registration, Gradio mount
    └── models.py    # Pydantic request/response schemas
```

**Layer rules:**
- `config/` imports nothing from `core/` or `api/`
- `core/` imports from `config/` only
- `api/` imports from `config/` and `core/`
- No circular imports between layers

**Tests (if added):**
```
tests/
├── test_ingestion.py
├── test_agent.py
└── test_api.py
```
Co-located by layer, not by file. `pytest` as runner.

### Format Patterns

**API responses:** Endpoint-specific (no generic wrapper).

```python
# POST /query — success
{"answer": "...", "sources": ["file.pdf", "https://..."]}

# POST /query — error
{"detail": "Qdrant is unreachable"}

# GET /health — success
{"status": "healthy"}
```

**Logging format:**
```python
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
```

Log agent tool calls at `INFO` level to satisfy observability requirement.

### Process Patterns

**Error handling:**
- Ingestion: catch per-document errors, log warning, continue pipeline
- Agent: let LlamaIndex handle tool errors internally; agent decides retry
- API: catch exceptions in endpoint, return `HTTPException(500, detail=str(e))`
- Startup: validate config immediately; raise `SystemExit` with clear message on failure

**Async patterns:**
- All runtime code is `async`/`await`
- Use `AsyncQdrantClient` alongside sync `QdrantClient` (ingestion can be sync)
- FastAPI endpoints are `async def`
- No `asyncio.run()` inside async context

**Import organization (enforced by ruff):**
1. Standard library
2. Third-party packages
3. Local imports (`from src.config...`)

### Enforcement Guidelines

**All AI agents implementing this project MUST:**
- Follow PEP 8 via `ruff` (auto-formatted on save)
- Respect layer boundaries (no imports from api/ in core/)
- Use `async def` for all API handlers and agent invocations
- Return endpoint-specific JSON (no generic wrappers)
- Log agent tool calls at INFO level
- Handle errors at the appropriate layer (don't bubble raw tracebacks to API responses)

## Project Structure & Boundaries

### Complete Project Directory Structure

```
info-retrieval-agent/
├── README.md
├── pyproject.toml              # PEP 621 metadata, dependencies, ruff config
├── uv.lock                     # Locked dependency versions
├── .env.example                # Documented env vars (committed)
├── .env                        # Actual secrets (gitignored)
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── main.py                     # Entry point: uvicorn app startup
├── ingest.py                   # Entry point: CLI ingestion script
├── data/
│   ├── pdfs/                   # PDF documents for ingestion
│   └── urls.txt                # URL list for web ingestion
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Pydantic BaseSettings class
│   │   └── providers.py        # get_llm(), get_embed_model(), get_vector_store()
│   ├── core/
│   │   ├── __init__.py
│   │   ├── ingestion.py        # IngestionPipeline: load, chunk, embed, push
│   │   ├── agent.py            # FunctionAgent + QueryEngineTool construction
│   │   └── vector_store.py     # Qdrant client, collection create, index setup
│   └── api/
│       ├── __init__.py
│       ├── app.py              # FastAPI app, routes, Gradio mount, lifespan
│       └── models.py           # QueryRequest, QueryResponse, HealthResponse
└── tests/                      # Optional for PoC
    ├── __init__.py
    ├── test_ingestion.py
    ├── test_agent.py
    └── test_api.py
```

### Architectural Boundaries

**Layer boundaries (strict):**

| Layer | Imports From | Exposes To |
|-------|-------------|------------|
| `config/` | stdlib, third-party only | `core/`, `api/`, entry points |
| `core/` | `config/`, third-party (LlamaIndex, Qdrant) | `api/`, entry points |
| `api/` | `config/`, `core/`, third-party (FastAPI, Gradio) | External HTTP clients |

**External boundaries:**

| Boundary | Protocol | Direction |
|----------|----------|----------|
| App → Qdrant | HTTP (port 6333) | Outbound (Docker network) |
| App → OpenAI | HTTPS | Outbound (internet) |
| Client → App | HTTP (port 8000) | Inbound (localhost only) |

### Requirements to Structure Mapping

| FR Category | Primary File(s) | Supporting Files |
|-------------|----------------|------------------|
| Document Ingestion (FR1-FR8) | `src/core/ingestion.py`, `ingest.py` | `src/config/providers.py`, `src/core/vector_store.py` |
| Agent & Retrieval (FR9-FR15) | `src/core/agent.py` | `src/core/vector_store.py`, `src/config/providers.py` |
| API (FR16-FR18) | `src/api/app.py`, `src/api/models.py` | `src/core/agent.py` |
| Chat Interface (FR19-FR20) | `src/api/app.py` (Gradio mount) | — |
| System Operations (FR21-FR24) | `docker-compose.yml`, `Dockerfile`, `src/config/settings.py` | `src/api/app.py` (lifespan) |
| Provider Abstraction (FR25-FR26) | `src/config/providers.py`, `src/config/settings.py` | — |

### Data Flow

```
[Ingestion Flow - Offline]
ingest.py → src/core/ingestion.py
  → SimpleDirectoryReader (PDFs) + trafilatura (URLs)
  → SentenceSplitter(512, 50)
  → OpenAIEmbedding + fastembed BM25
  → QdrantVectorStore (push)

[Query Flow - Runtime]
Client → POST /query → src/api/app.py
  → src/core/agent.py (FunctionAgent.run())
    → QueryEngineTool → VectorStoreIndex → Qdrant (hybrid search)
    → [optional re-query loop]
  → synthesized answer + sources
  → JSON response → Client
```

### Development Workflow

| Command | Purpose |
|---------|--------|
| `uv sync` | Install dependencies from lock file |
| `uv run python ingest.py` | Run ingestion locally (requires Qdrant running) |
| `uv run python main.py` | Run app server locally |
| `docker compose up` | Run full system (Qdrant + App) |
| `docker compose up qdrant` | Run only Qdrant (for local dev) |
| `uv run ruff check .` | Lint |
| `uv run ruff format .` | Format |
| `uv run pytest` | Run tests |

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
- All LlamaIndex packages (core, llms-openai, embeddings-openai, vector-stores-qdrant) compatible within v0.14.x
- FastAPI + uvicorn + Gradio co-hosting is a documented, supported pattern
- pydantic-settings aligns with FastAPI’s native Pydantic usage
- `uv` supports PEP 621 `pyproject.toml` natively
- Docker Compose v2 with `python:3.12-slim` runs all chosen libraries without issue

**Pattern Consistency:**
- snake_case used uniformly: Python code, API JSON fields, Qdrant payload fields
- Async used consistently: FastAPI handlers, LlamaIndex agent, AsyncQdrantClient
- Layer boundaries are clear and unidirectional (config → core → api)

### Requirements Coverage ✅

| FR Category | Architectural Support | Status |
|-------------|----------------------|--------|
| Document Ingestion (FR1-8) | `core/ingestion.py` + IngestionPipeline + trafilatura | ✅ |
| Agent & Retrieval (FR9-15) | `core/agent.py` + FunctionAgent + hybrid QueryEngineTool | ✅ |
| API (FR16-18) | `api/app.py` + FastAPI + auto OpenAPI | ✅ |
| Chat Interface (FR19-20) | Gradio mount on FastAPI | ✅ |
| System Operations (FR21-24) | Docker Compose + pydantic-settings + lifespan validation | ✅ |
| Provider Abstraction (FR25-26) | `config/providers.py` factory functions + env vars | ✅ |

**NFR Coverage:**
- Performance (60s timeout): Agent timeout parameter + FastAPI request timeout ✅
- Maintainability (3-layer): Enforced by structure and layer rules ✅
- Integration (OpenAI + Qdrant): Both documented in external boundaries ✅

### Implementation Readiness ✅

- All critical decisions have specific technology + version + rationale
- Naming, structure, format, process, and async patterns defined with examples
- Full directory tree with every file named and purpose documented

### Architecture Completeness Checklist

- [x] Project context analyzed and scale assessed
- [x] Technology stack fully specified with versions
- [x] All critical architectural decisions documented
- [x] Implementation patterns defined with examples
- [x] Complete project directory structure
- [x] Layer boundaries and import rules established
- [x] FR → file mapping complete
- [x] Data flow diagrams for both runtime paths
- [x] Development workflow commands documented
- [x] Error handling patterns per layer
- [x] Async consistency enforced

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High — simple system, well-researched stack, all decisions aligned

**First Implementation Priority:**
Project scaffolding: `uv init`, create directory structure, write `pyproject.toml` with full dependency list, create `.env.example`.
