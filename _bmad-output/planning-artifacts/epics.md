---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
---

# info-retrieval-agent - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for info-retrieval-agent, decomposing the requirements from the PRD and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

- FR1: Developer can ingest PDF files from a local directory into the vector store
- FR2: Developer can ingest web pages from a URL list file into the vector store
- FR3: System chunks documents into appropriately-sized segments with overlap for context continuity
- FR4: System generates vector embeddings for all chunks and stores them in Qdrant
- FR5: System generates sparse (BM25) vectors alongside dense embeddings for hybrid search
- FR6: Developer can see progress output during ingestion (files processed, chunks stored)
- FR7: System reports errors for individual documents (malformed PDF, unreachable URL) without halting the entire pipeline
- FR8: System preserves source metadata (filename, URL, page number) with each stored chunk
- FR9: Developer can submit a natural-language question and receive a synthesized answer
- FR10: Agent formulates search queries against the vector store autonomously
- FR11: Agent reformulates queries and performs follow-up searches when initial results are insufficient
- FR12: Agent synthesizes a coherent natural-language answer from retrieved context
- FR13: Agent includes source attribution (document names/URLs) in responses
- FR14: Agent responds with a clear "I don't know" message when the knowledge base has no relevant content
- FR15: Agent uses hybrid search (dense + sparse) for retrieval
- FR16: System exposes a `POST /query` endpoint accepting a JSON question and returning a JSON answer with sources
- FR17: System returns appropriate HTTP error codes (422/500) with descriptive messages
- FR18: System provides automatic OpenAPI documentation at `/docs`
- FR19: Developer can interact with the agent via a web-based chat UI
- FR20: Chat UI is accessible at the same host/port as the API (co-hosted)
- FR21: System starts via `docker compose up` with no additional manual steps beyond providing an API key
- FR22: System reads LLM/embedding provider configuration from environment variables
- FR23: Ingested data persists across container restarts without re-ingestion
- FR24: System fails fast with a clear error message when required configuration (API key) is missing or invalid
- FR25: System supports swapping LLM provider via environment variable without code changes
- FR26: System supports swapping embedding provider via environment variable (with re-ingestion required)

### NonFunctional Requirements

- NFR1: Agent query responses complete within 60 seconds
- NFR2: Ingestion pipeline processes a 10-document corpus within 5 minutes
- NFR3: System startup completes within 30 seconds
- NFR4: System depends on OpenAI API availability for all LLM and embedding operations
- NFR5: System depends on local Qdrant container reachable via Docker network
- NFR6: Codebase follows a clear 3-layer structure (config / core / api)
- NFR7: Dependencies pinned in `pyproject.toml`; `.env.example` documents all env vars

### Additional Requirements

- No starter template — manual scaffolding (`uv init`, directory structure, `pyproject.toml`)
- `pydantic-settings` for typed configuration with validation at startup
- Provider factory functions (`get_llm()`, `get_embed_model()`, `get_vector_store()`)
- Qdrant collection created with payload indexes (`source_type`, `file_name`) at init
- `python:3.12-slim` Docker base image
- `ruff` for linting/formatting
- Layer boundary enforcement: config → core → api (unidirectional)
- Implementation sequence: scaffolding → config → vector store → ingestion → agent → API → Docker

### UX Design Requirements

N/A — No UX design document. Gradio provides the chat UI out of the box.

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR1 | Epic 2 | Ingest PDFs from directory |
| FR2 | Epic 2 | Ingest web pages from URL list |
| FR3 | Epic 2 | Chunk documents with overlap |
| FR4 | Epic 2 | Generate embeddings, store in Qdrant |
| FR5 | Epic 2 | Generate BM25 sparse vectors |
| FR6 | Epic 2 | Progress output during ingestion |
| FR7 | Epic 2 | Per-document error resilience |
| FR8 | Epic 2 | Preserve source metadata |
| FR9 | Epic 3 | Submit question, receive answer |
| FR10 | Epic 3 | Agent formulates queries autonomously |
| FR11 | Epic 3 | Agent reformulates on insufficient results |
| FR12 | Epic 3 | Agent synthesizes coherent answer |
| FR13 | Epic 3 | Source attribution in responses |
| FR14 | Epic 3 | "I don't know" when no relevant content |
| FR15 | Epic 3 | Hybrid search (dense + sparse) |
| FR16 | Epic 4 | POST /query endpoint |
| FR17 | Epic 4 | HTTP error codes (422/500) |
| FR18 | Epic 4 | OpenAPI docs at /docs |
| FR19 | Epic 4 | Gradio chat UI |
| FR20 | Epic 4 | Chat UI co-hosted with API |
| FR21 | Epic 5 | Start via docker compose up |
| FR22 | Epic 1 | Config from environment variables |
| FR23 | Epic 5 | Data persists across restarts |
| FR24 | Epic 1 | Fail fast on missing config |
| FR25 | Epic 1 | Swap LLM provider via env var |
| FR26 | Epic 1 | Swap embedding provider via env var |

## Epic List

### Epic 1: Project Foundation & Configuration
Developer has a runnable Python project with typed configuration, provider factories, and Qdrant connectivity — the base upon which all features are built.
**FRs covered:** FR22, FR24, FR25, FR26
**NFRs covered:** NFR6, NFR7

### Epic 2: Document Ingestion Pipeline
Developer can ingest PDFs and web pages into Qdrant via CLI, with hybrid vectors, metadata preservation, progress reporting, and error resilience.
**FRs covered:** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8

### Epic 3: Agentic Retrieval & Synthesis
Developer can submit a question and receive an intelligent, source-attributed answer from the agent, which autonomously searches, reformulates, and synthesizes.
**FRs covered:** FR9, FR10, FR11, FR12, FR13, FR14, FR15
**NFRs covered:** NFR1

### Epic 4: API & Chat Interface
Developer can access the agent via a REST endpoint and a Gradio chat UI, both co-hosted on the same FastAPI server.
**FRs covered:** FR16, FR17, FR18, FR19, FR20

### Epic 5: Docker Compose Packaging
Developer can start the full system (Qdrant + App) with a single `docker compose up` command, with persistent data across restarts.
**FRs covered:** FR21, FR23
**NFRs covered:** NFR3, NFR5

## Epic 1: Project Foundation & Configuration

Developer has a runnable Python project with typed configuration, provider factories, and Qdrant connectivity — the base upon which all features are built.

### Story 1.1: Project Scaffolding

As a developer,
I want a properly structured Python project with all dependencies defined,
So that I have a clean foundation to build features on.

**Acceptance Criteria:**

**Given** a fresh directory
**When** the project is scaffolded with `uv init` and the directory structure is created
**Then** the project has the 3-layer structure (`src/config/`, `src/core/`, `src/api/`) with `__init__.py` files
**And** `pyproject.toml` contains all required dependencies (llama-index-core, llama-index-llms-openai, llama-index-embeddings-openai, llama-index-vector-stores-qdrant, qdrant-client, fastapi, uvicorn, gradio, pydantic-settings, python-dotenv, trafilatura, fastembed)
**And** `ruff` is configured in `pyproject.toml` for linting and formatting
**And** `.gitignore` excludes `.env`, `__pycache__/`, `.venv/`, `data/pdfs/`
**And** `uv sync` installs all dependencies without errors

### Story 1.2: Configuration & Settings

As a developer,
I want typed, validated configuration loaded from environment variables,
So that the system fails fast with clear messages when misconfigured.

**Acceptance Criteria:**

**Given** a `pydantic-settings` BaseSettings class in `src/config/settings.py`
**When** `OPENAI_API_KEY` is present in `.env`
**Then** settings load successfully with all defaults resolved (QDRANT_HOST=localhost, QDRANT_PORT=6333, LLM_PROVIDER=openai, LLM_MODEL=gpt-4o-mini, EMBED_MODEL=text-embedding-3-small)
**And** `.env.example` documents all required and optional environment variables

**Given** `OPENAI_API_KEY` is missing or empty
**When** the settings are instantiated
**Then** the application raises a clear error message indicating the missing key and exits

### Story 1.3: Provider Factory Functions

As a developer,
I want factory functions that create LLM, embedding, and vector store instances from config,
So that I can swap providers by changing environment variables without code changes.

**Acceptance Criteria:**

**Given** `src/config/providers.py` with `get_llm()`, `get_embed_model()`, and `get_vector_store()` functions
**When** `LLM_PROVIDER=openai` and `LLM_MODEL=gpt-4o-mini`
**Then** `get_llm()` returns a LlamaIndex OpenAI LLM instance configured with the specified model

**Given** `EMBED_PROVIDER=openai` and `EMBED_MODEL=text-embedding-3-small`
**When** `get_embed_model()` is called
**Then** it returns an OpenAIEmbedding instance with 1536 dimensions

**Given** `QDRANT_HOST` and `QDRANT_PORT` are configured
**When** `get_vector_store()` is called
**Then** it returns a QdrantVectorStore configured with collection name `knowledge_base`, hybrid search enabled, and both sync and async clients initialized

## Epic 2: Document Ingestion Pipeline

Developer can ingest PDFs and web pages into Qdrant via CLI, with hybrid vectors, metadata preservation, progress reporting, and error resilience.

### Story 2.1: Qdrant Collection Setup

As a developer,
I want the Qdrant collection created with proper vector configuration and payload indexes,
So that ingested documents are stored optimally for hybrid search.

**Acceptance Criteria:**

**Given** a running Qdrant instance and `src/core/vector_store.py`
**When** the collection setup function is called
**Then** a collection named `knowledge_base` is created with dense vectors (1536 dims, cosine distance) and sparse vector config for BM25
**And** payload indexes are created for `source_type` (keyword) and `file_name` (keyword)
**And** if the collection already exists, it is not recreated or overwritten

### Story 2.2: PDF Document Loading

As a developer,
I want to load PDF files from a local directory,
So that their content is available for chunking and embedding.

**Acceptance Criteria:**

**Given** PDF files in `./data/pdfs/`
**When** the PDF loader is invoked
**Then** all `.pdf` files in the directory are loaded as LlamaIndex Document objects
**And** each document's metadata includes `file_name`, `file_path`, and `source_type: "pdf"`

**Given** a malformed or unreadable PDF in the directory
**When** the loader processes it
**Then** the error is logged as a warning with the filename
**And** processing continues with remaining files

### Story 2.3: Web Page Loading

As a developer,
I want to load web pages from a URL list file,
So that web content is available for chunking and embedding.

**Acceptance Criteria:**

**Given** a file at `./data/urls.txt` with one URL per line
**When** the web loader is invoked
**Then** each URL is fetched and content extracted via `trafilatura`
**And** each document's metadata includes `source_url` and `source_type: "web"`

**Given** an unreachable URL or one that returns no extractable content
**When** the loader processes it
**Then** the error is logged as a warning with the URL
**And** processing continues with remaining URLs

### Story 2.4: Ingestion Pipeline (Chunking, Embedding, Storage)

As a developer,
I want documents chunked, embedded (dense + sparse), and pushed to Qdrant,
So that the knowledge base is populated and ready for hybrid search queries.

**Acceptance Criteria:**

**Given** a list of loaded Document objects (from PDFs and/or web pages)
**When** the IngestionPipeline runs
**Then** documents are split using `SentenceSplitter(chunk_size=512, chunk_overlap=50)`
**And** dense embeddings are generated via `text-embedding-3-small`
**And** sparse BM25 vectors are generated via `fastembed`
**And** all chunks are pushed to the `knowledge_base` Qdrant collection with preserved metadata (filename/URL, source_type)

### Story 2.5: CLI Ingestion Script with Progress Reporting

As a developer,
I want a CLI entry point that orchestrates the full ingestion flow with progress output,
So that I can populate the knowledge base by running a single command.

**Acceptance Criteria:**

**Given** `ingest.py` as the CLI entry point
**When** `python ingest.py` is run (with Qdrant available and `.env` configured)
**Then** it loads PDFs from `./data/pdfs/` and URLs from `./data/urls.txt`
**And** runs the ingestion pipeline (chunk → embed → store)
**And** prints progress: number of files found, documents loaded, chunks created, and total vectors stored
**And** reports any per-document errors encountered during loading
**And** completes a 10-document corpus within 5 minutes (NFR2)

## Epic 3: Agentic Retrieval & Synthesis

Developer can submit a question and receive an intelligent, source-attributed answer from the agent, which autonomously searches, reformulates, and synthesizes.

### Story 3.1: Vector Store Index & Query Engine

As a developer,
I want a VectorStoreIndex over the Qdrant collection with hybrid search configured,
So that the agent has a retrieval tool that combines dense and sparse search.

**Acceptance Criteria:**

**Given** an existing `knowledge_base` collection in Qdrant with ingested documents
**When** the index and query engine are constructed in `src/core/agent.py`
**Then** a `VectorStoreIndex` is created from the existing vector store
**And** a query engine is configured with `similarity_top_k=5`, `sparse_top_k=12`, and `vector_store_query_mode="hybrid"`
**And** the query engine is wrapped as a `QueryEngineTool` with a descriptive name and description

### Story 3.2: FunctionAgent with Multi-Step Retrieval

As a developer,
I want a FunctionAgent that uses the query engine tool to answer questions, reformulating queries when needed,
So that I get intelligent answers that go beyond single-shot retrieval.

**Acceptance Criteria:**

**Given** a `FunctionAgent` constructed with the QueryEngineTool and GPT-4o-mini
**When** a question is submitted via `await agent.run(user_msg=...)`
**Then** the agent autonomously formulates a search query and calls the knowledge_base tool
**And** if initial results are insufficient, the agent reformulates and issues follow-up searches
**And** the agent synthesizes a coherent natural-language answer from retrieved context
**And** the response completes within 60 seconds (NFR1)

**Given** the system prompt instructs the agent on behavior
**When** the agent is constructed
**Then** the system prompt enforces: always use the tool before answering, cite sources, admit ignorance when appropriate, and allow re-querying

### Story 3.3: Source Attribution & "I Don't Know" Behavior

As a developer,
I want the agent to cite its sources and clearly indicate when it cannot find relevant information,
So that I can trust the answers and know the system's limitations.

**Acceptance Criteria:**

**Given** the agent finds relevant information in the knowledge base
**When** it synthesizes an answer
**Then** the response includes source attribution (document filenames and/or URLs)
**And** sources are extractable from the agent's response for the API layer to format

**Given** a question about a topic not covered in the knowledge base
**When** the agent searches and finds no relevant content
**Then** it responds with a clear message like "I could not find information about this in the knowledge base"
**And** it does NOT hallucinate an answer from general knowledge

## Epic 4: API & Chat Interface

Developer can access the agent via a REST endpoint and a Gradio chat UI, both co-hosted on the same FastAPI server.

### Story 4.1: FastAPI Application & Query Endpoint

As a developer,
I want a FastAPI app with a `POST /query` endpoint that invokes the agent and returns structured JSON,
So that I can programmatically query the knowledge base.

**Acceptance Criteria:**

**Given** `src/api/app.py` with a FastAPI application and `src/api/models.py` with Pydantic schemas
**When** a POST request is sent to `/query` with `{"question": "some question"}`
**Then** the agent is invoked with the question
**And** the response is `{"answer": "...", "sources": ["file.pdf", "https://..."]}`
**And** OpenAPI documentation is automatically available at `/docs`

**Given** a request with missing or invalid `question` field
**When** it hits `/query`
**Then** FastAPI returns HTTP 422 with a descriptive validation error

**Given** the agent or Qdrant encounters an internal error
**When** the request is processed
**Then** the endpoint returns HTTP 500 with `{"detail": "descriptive error message"}`
**And** the raw traceback is NOT exposed to the client

### Story 4.2: Gradio Chat UI

As a developer,
I want a Gradio chat interface mounted on the FastAPI app,
So that I can interactively query the knowledge base through a web UI.

**Acceptance Criteria:**

**Given** a Gradio `ChatInterface` configured in `src/api/app.py`
**When** the app server is running
**Then** the chat UI is accessible at `/chat` on the same host and port as the API
**And** submitting a message through the chat UI invokes the agent and displays the answer
**And** no separate process or port is required (co-hosted via `gr.mount_gradio_app`)

### Story 4.3: Application Lifespan & Server Entry Point

As a developer,
I want a `main.py` entry point that starts the server with proper initialization,
So that the app validates configuration and sets up resources before serving requests.

**Acceptance Criteria:**

**Given** `main.py` as the server entry point
**When** `python main.py` is run
**Then** uvicorn starts the FastAPI app on `0.0.0.0:8000`
**And** configuration is validated at startup (fail fast on missing API key)
**And** the agent and vector store are initialized during app lifespan
**And** agent tool calls are logged at INFO level (observable in console output)

## Epic 5: Docker Compose Packaging

Developer can start the full system (Qdrant + App) with a single `docker compose up` command, with persistent data across restarts.

### Story 5.1: Dockerfile & Docker Compose

As a developer,
I want a Dockerfile for the app and a Docker Compose configuration for the full system,
So that I can run everything with a single `docker compose up` command.

**Acceptance Criteria:**

**Given** a `Dockerfile` using `python:3.12-slim` base image
**When** the image is built
**Then** it installs dependencies via `uv`, copies source code, and sets `main.py` as the entry point
**And** the image size is reasonable (no dev dependencies or unnecessary files)

**Given** a `docker-compose.yml` with two services (qdrant + app)
**When** `docker compose up` is run with a valid `.env` file
**Then** Qdrant starts and becomes available on the Docker network
**And** the app container starts, connects to Qdrant via service name (`qdrant:6333`), and serves on port 8000
**And** the system is ready to serve queries within 30 seconds (NFR3)
**And** no manual steps are required beyond providing the API key in `.env`

**Given** Qdrant data was previously ingested
**When** `docker compose down` followed by `docker compose up` is run
**Then** the Qdrant data persists via a named Docker volume (`qdrant_data`)
**And** previously ingested documents are queryable without re-ingestion
