# Info Retrieval Agent — Source Tree Analysis

**Date:** 2026-04-29

## Overview

A compact Python application with clear separation between configuration, core logic (agent + ingestion + vector store), and API layer. Two entry points serve distinct purposes: `main.py` for the web server and `ingest.py` for the document loading CLI.

## Complete Directory Structure

```
info-retrieval-agent-docs/
├── main.py                     # Server entry point (uvicorn → FastAPI)
├── ingest.py                   # CLI entry point (load → chunk → embed → store)
├── pyproject.toml              # Project metadata, dependencies, ruff config
├── uv.lock                     # Lockfile for reproducible installs
├── Dockerfile                  # Python 3.12-slim + uv, production image
├── docker-compose.yml          # App + Qdrant services
├── README.md                   # User-facing documentation
├── .env.example                # Template for environment variables
│
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Pydantic BaseSettings — typed env-var config
│   │   └── providers.py        # Factory functions: get_llm(), get_embed_model(), get_vector_store()
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py            # FunctionAgent construction, QueryEngineTool, source capture
│   │   ├── ingestion.py        # PDF loading, web/PMC fetching, chunking pipeline
│   │   └── vector_store.py     # Qdrant collection creation (dense + sparse vectors)
│   └── api/
│       ├── __init__.py
│       ├── app.py              # FastAPI app, /query + /health routes, Gradio mount
│       └── models.py           # Pydantic request/response schemas
│
├── data/
│   ├── pdfs/                   # Drop PDF files here for ingestion
│   └── urls.txt                # One URL per line; supports PMC articles
│
└── tests/
    ├── __init__.py
    ├── test_agent.py           # Agent construction tests
    ├── test_api.py             # FastAPI endpoint tests
    ├── test_ingestion.py       # Ingestion pipeline unit tests
    ├── test_providers.py       # Provider factory tests
    ├── test_settings.py        # Settings validation tests
    ├── test_vector_store.py    # Vector store setup tests
    └── e2e/
        ├── __init__.py
        ├── test_ingestion_e2e.py   # End-to-end ingestion tests
        └── test_query_e2e.py       # End-to-end query tests
```

## Critical Directories

### `src/config/`

**Purpose:** Centralized configuration and dependency construction.
**Contains:** Pydantic settings class (validates env vars at startup) and factory functions that instantiate LLM, embedding model, and vector store clients based on config.

### `src/core/`

**Purpose:** Business logic — the three pillars of the system.
**Contains:**
- `agent.py` — Builds the FunctionAgent with a QueryEngineTool over the Qdrant index; includes source-node capture via monkey-patched tool methods.
- `ingestion.py` — Document loading (PDF via SimpleDirectoryReader, web via trafilatura, PMC via Europe PMC/NCBI APIs), then chunking + embedding via IngestionPipeline.
- `vector_store.py` — Idempotent Qdrant collection creation with dense (cosine) + sparse (BM25) vector configs and payload indexes.

### `src/api/`

**Purpose:** HTTP interface layer.
**Contains:** FastAPI application with async lifespan (agent init), POST /query endpoint, GET /health endpoint, and a Gradio ChatInterface mounted at /chat.

### `data/`

**Purpose:** Input data for ingestion.
**Contains:** `pdfs/` subdirectory for PDF documents and `urls.txt` for web page URLs. These are read by `ingest.py` at runtime.

### `tests/`

**Purpose:** Test suite (pytest).
**Contains:** Unit tests for each module + e2e tests that require a running Qdrant instance.

## Entry Points

- **Main Entry:** `main.py` — validates config, then starts uvicorn serving `src.api.app:app` on port 8000.
- **Ingestion CLI:** `ingest.py` — validates config, loads PDFs + web docs, runs ingestion pipeline, reports chunk count.

## Configuration Files

- **`pyproject.toml`** — Project metadata, dependencies, ruff linting rules
- **`docker-compose.yml`** — Two services: `qdrant` (persistent volume) and `app` (built from Dockerfile, depends on qdrant)
- **`Dockerfile`** — Python 3.12-slim base, installs uv, syncs deps, copies source, CMD runs main.py
- **`.env` / `.env.example`** — Runtime configuration (API keys, provider choices, model names, Qdrant connection)

## File Organization Patterns

| Pattern | Purpose | Examples |
|---------|---------|---------|
| `src/<layer>/<module>.py` | Clean layered architecture | `src/config/settings.py`, `src/core/agent.py` |
| `tests/test_<module>.py` | Mirror source structure | `tests/test_agent.py` |
| `tests/e2e/test_*_e2e.py` | Integration tests needing infra | `tests/e2e/test_query_e2e.py` |

## Notes for Development

- All imports use absolute paths from project root (`from src.config.settings import ...`)
- Heavy imports (LlamaIndex, IngestionPipeline) are deferred inside functions to speed up startup validation
- The `ensure_collection()` function is idempotent — safe to call on every ingestion run
- Source capture relies on a module-level `_last_sources` list that is cleared before each request — not thread-safe for concurrent requests (acceptable for PoC)
- Ruff is configured with `line-length = 120` and excludes `.pi`, `.opencode`, `_bmad`, `_bmad-output` directories

---

_Generated using BMAD Method `document-project` workflow_
