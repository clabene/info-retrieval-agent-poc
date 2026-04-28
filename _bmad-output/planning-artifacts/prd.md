---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish']
inputDocuments:
  - '_bmad-output/planning-artifacts/research/technical-llamaindex-agentic-patterns-research-2026-04-22.md'
  - '_bmad-output/brainstorming/brainstorming-session-2026-04-15-1730.md'
workflowType: 'prd'
documentCounts:
  briefs: 0
  research: 1
  brainstorming: 1
  projectDocs: 0
  projectContext: 0
classification:
  projectType: api_backend
  domain: scientific
  complexity: medium
  projectContext: greenfield
---

# Product Requirements Document - info-retrieval-agent

**Author:** clabene
**Date:** 2026-04-27

## Executive Summary

A proof-of-concept agentic information-retrieval system that ingests documents (PDFs and web pages), stores them as vector embeddings in Qdrant, and exposes a single-endpoint query API backed by a LlamaIndex FunctionAgent. The agent autonomously reformulates queries, retrieves relevant context via hybrid search (dense + BM25), evaluates sufficiency, and synthesizes natural-language answers — going beyond naive RAG by reasoning about *how* to search, not just *what* to return.

The system runs entirely locally via Docker Compose (2 containers: Qdrant + App), uses OpenAI APIs for embeddings and LLM inference (BYOK via environment variable), and provides both a programmatic REST endpoint (`POST /query`) and an interactive Gradio chat UI. Ingestion is offline via CLI script.

Primary purpose: hands-on learning across the full agentic RAG stack — embeddings, vector databases, agent orchestration, API design, containerization — integrated into one coherent, working system.

### What Makes This Special

This is not a production product competing in the RAG space. Its value is **breadth of integration as a learning vehicle** — a single project that exercises every layer of a modern AI retrieval system end-to-end. Success is measured by "it works locally and I understand every piece," not by user adoption or performance benchmarks.

The core insight: deeply understanding agentic RAG requires building the full pipeline yourself — from document chunking through vector storage to multi-step agent reasoning — rather than consuming pre-built tutorial fragments in isolation.

## Project Classification

| Dimension | Value |
|-----------|-------|
| **Project Type** | API Backend (with lightweight chat UI) |
| **Domain** | Scientific / AI-ML Tooling |
| **Complexity** | Medium — novel technology, no regulatory constraints |
| **Project Context** | Greenfield |

## Success Criteria

### User Success

- Ingest a set of PDFs and web URLs via CLI, then query the system and receive correct, contextually-grounded answers
- The agent demonstrably reformulates queries and performs multi-step retrieval when initial results are insufficient
- Every component (ingestion, vector store, agent, API, UI, containerization) is understood well enough to explain and modify

### Technical Success

- `docker compose up` brings the full system online with zero manual intervention beyond providing an API key
- `POST /query` returns a synthesized answer with source attribution
- Gradio chat UI is accessible and functional at the same endpoint
- Agent correctly responds "I don't know" when the knowledge base has no relevant content
- Qdrant data persists across container restarts (Docker volume)
- Provider-swappable architecture: changing LLM requires only env var changes, not code changes

### Measurable Outcomes

| Outcome | Measure |
|---------|--------|
| End-to-end functionality | Binary — system ingests, retrieves, and answers correctly |
| Agentic behavior | Agent issues ≥2 tool calls on complex queries (observable in logs) |
| Stack breadth | All 7 technologies exercised: LlamaIndex, Qdrant, OpenAI, FastAPI, Gradio, Docker, Python |

## Product Scope & Phased Development

### MVP Strategy

**Approach:** End-to-end proof of concept — every layer works, nothing is mocked or stubbed. The MVP is "complete" when all 7 technologies are exercised in a single working system.

**Resource Requirements:** Solo developer, OpenAI API key, local Docker environment.

### MVP Feature Set (Phase 1)

**Core Journeys Supported:** All three (querying, ingesting, operating)

**Must-Have Capabilities:**
- Offline CLI ingestion (PDFs from folder + URLs from file)
- Qdrant vector storage with hybrid search (dense + BM25)
- FunctionAgent with QueryEngineTool for multi-step retrieval
- `POST /query` REST endpoint returning answer + sources
- Gradio chat UI mounted on FastAPI
- Docker Compose packaging (2 containers)
- OpenAI BYOK via `OPENAI_API_KEY` env var
- Provider-swappable architecture (env var config)

### Phase 2 — Polish

- Streaming responses via SSE (`POST /query/stream`)
- Validated Ollama/Anthropic provider swap
- OpenTelemetry observability for tracing agent reasoning
- Evaluation pipeline (faithfulness + relevancy metrics)

### Phase 3 — Expansion

- Live cloud deployment
- Upload API for dynamic ingestion (not just offline CLI)
- Multi-collection support (separate knowledge bases)
- Conversation memory (multi-turn chat with Context persistence)

### Risk Mitigation Strategy

| Risk | Impact | Mitigation |
|------|--------|------------|
| LlamaIndex API changes | Rework agent/ingestion code | Pin `llama-index-core` version in `pyproject.toml` |
| Poor PDF parsing quality | Bad retrieval results | Start with default pypdf; upgrade to `unstructured` if needed |
| Hybrid search complexity | Blocks MVP completion | Fall back to dense-only search; add BM25 as enhancement |
| OpenAI rate limits during dev | Slow iteration | Use small test corpus; cache embeddings via IngestionPipeline |
| Docker memory pressure | Containers crash | Qdrant + App only (no Ollama); monitor with `docker stats` |

## User Journeys

### Journey 1: Querying the Knowledge Base (Happy Path)

**Persona:** Claudio, developer exploring agentic RAG, has already ingested a collection of technical PDFs and documentation URLs.

**Scene:** Opens the Gradio chat UI (or fires a curl request at `POST /query`) and types a question about content spread across multiple ingested documents.

**Flow:**
1. Submits natural-language question via chat UI or API
2. Agent receives query, formulates a search against the vector store
3. Initial retrieval returns partially relevant chunks — agent reformulates and searches again
4. Agent synthesizes a coherent answer from retrieved context, citing source documents
5. Response appears in the UI (or JSON response body) with the answer and source attribution

**Success moment:** The answer is correct, draws from the right documents, and the agent made multiple tool calls to get there (observable in logs).

**Failure scenario:** The question is about something not in the knowledge base. Agent responds clearly: "I could not find information about this in the knowledge base." — no hallucination.

### Journey 2: Ingesting Documents

**Flow:**
1. Places PDF files in `./data/pdfs/` folder
2. Adds target URLs to `./data/urls.txt`
3. Runs `python ingest.py`
4. Script loads documents, chunks them, generates embeddings, pushes to Qdrant
5. Progress output shows files processed and chunks stored
6. Ingestion completes — knowledge base is ready for queries

**Success moment:** Script finishes without errors, and a subsequent query returns content from the just-ingested documents.

**Failure scenario:** A malformed PDF or unreachable URL — script reports the error clearly and continues processing remaining documents.

### Journey 3: Operating the System

**Flow:**
1. Sets `OPENAI_API_KEY` in `.env` file
2. Runs `docker compose up`
3. Qdrant starts, app container starts, connects to Qdrant
4. Previously ingested data is still there (persisted volume) — no re-ingestion needed
5. After the session, `docker compose down` stops everything cleanly; data survives

**Success moment:** From cold start to working query in under 60 seconds.

**Failure scenario:** Missing or invalid API key — app fails fast with a clear error message, not a cryptic traceback.

### Journey Requirements Summary

| Journey | Capabilities Revealed |
|---------|----------------------|
| Querying | Agent orchestration, multi-step retrieval, source attribution, "I don't know" behavior, API endpoint, chat UI |
| Ingesting | CLI script, PDF loader, web loader, chunking pipeline, embedding generation, Qdrant push, progress reporting, error resilience |
| Operating | Docker Compose config, persistent volumes, env var configuration, clear error messages on misconfiguration |

## API Backend Specific Requirements

### API Surface

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/query` | POST | Submit a natural-language question, receive a synthesized answer |
| `/chat` | GET | Gradio chat UI (mounted on FastAPI) |
| `/health` | GET | Optional — include only if trivial to add |

### Request/Response Schemas

**POST /query**

Request:
```json
{
  "question": "string"
}
```

Response:
```json
{
  "answer": "string",
  "sources": ["string"]
}
```

**Error response:**
```json
{
  "detail": "string"
}
```

### Technical Architecture Considerations

- **No authentication** — API is open, intended for local use only
- **No rate limiting** — single user, no abuse vector
- **No versioning** — PoC scope, no backwards-compatibility concerns
- **JSON only** — no content negotiation, no XML/protobuf
- **Async handlers** — FastAPI async endpoints calling async LlamaIndex agent
- FastAPI provides automatic OpenAPI docs at `/docs` (free Swagger UI)
- Pydantic models for request/response validation
- Single `uvicorn` process — no Gunicorn/workers needed for a PoC
- Error handling: 500 with clear message on agent/Qdrant failures, 422 on malformed input (FastAPI default)

## Functional Requirements

### Document Ingestion

- FR1: Developer can ingest PDF files from a local directory into the vector store
- FR2: Developer can ingest web pages from a URL list file into the vector store
- FR3: System chunks documents into appropriately-sized segments with overlap for context continuity
- FR4: System generates vector embeddings for all chunks and stores them in Qdrant
- FR5: System generates sparse (BM25) vectors alongside dense embeddings for hybrid search
- FR6: Developer can see progress output during ingestion (files processed, chunks stored)
- FR7: System reports errors for individual documents (malformed PDF, unreachable URL) without halting the entire pipeline
- FR8: System preserves source metadata (filename, URL, page number) with each stored chunk

### Information Retrieval & Agent

- FR9: Developer can submit a natural-language question and receive a synthesized answer
- FR10: Agent formulates search queries against the vector store autonomously
- FR11: Agent reformulates queries and performs follow-up searches when initial results are insufficient
- FR12: Agent synthesizes a coherent natural-language answer from retrieved context
- FR13: Agent includes source attribution (document names/URLs) in responses
- FR14: Agent responds with a clear "I don't know" message when the knowledge base has no relevant content
- FR15: Agent uses hybrid search (dense + sparse) for retrieval

### API

- FR16: System exposes a `POST /query` endpoint accepting a JSON question and returning a JSON answer with sources
- FR17: System returns appropriate HTTP error codes (422 for malformed input, 500 for internal failures) with descriptive messages
- FR18: System provides automatic OpenAPI documentation at `/docs`

### Chat Interface

- FR19: Developer can interact with the agent via a web-based chat UI
- FR20: Chat UI is accessible at the same host/port as the API (co-hosted)

### System Operations

- FR21: System starts via `docker compose up` with no additional manual steps beyond providing an API key
- FR22: System reads LLM/embedding provider configuration from environment variables
- FR23: Ingested data persists across container restarts without re-ingestion
- FR24: System fails fast with a clear error message when required configuration (API key) is missing or invalid

### Provider Abstraction

- FR25: System supports swapping LLM provider via environment variable without code changes
- FR26: System supports swapping embedding provider via environment variable (with re-ingestion required)

## Non-Functional Requirements

### Performance

- Agent query responses complete within 60 seconds (accounts for multi-step retrieval + OpenAI latency)
- Ingestion pipeline processes a 10-document corpus (mixed PDFs + URLs) within 5 minutes
- System startup (`docker compose up` → ready to serve) completes within 30 seconds

### Integration

- System depends on OpenAI API availability for all LLM and embedding operations
- System depends on local Qdrant container reachable via Docker network
- No other external integrations required

### Maintainability

- Codebase follows a clear 3-layer structure (config / core / api) for readability
- Dependencies pinned in `pyproject.toml` to prevent breakage from upstream changes
- `.env.example` provided documenting all required and optional environment variables
