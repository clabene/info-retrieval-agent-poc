# Info Retrieval Agent — Project Overview

**Date:** 2026-04-29
**Type:** Agentic RAG system (proof of concept)
**Architecture:** FunctionAgent + hybrid vector search

## Executive Summary

This project implements a self-contained information retrieval system that combines document ingestion, vector storage, and an autonomous LLM agent. Users ingest PDFs and web pages into a Qdrant vector database, then query the knowledge base through a FastAPI endpoint or Gradio chat UI. The LlamaIndex FunctionAgent autonomously decides how to search, reformulates queries when initial results are insufficient, and synthesizes answers with source citations.

## Project Classification

- **Repository Type:** Single application
- **Project Type:** Backend API + CLI tool
- **Primary Language:** Python 3.12
- **Architecture Pattern:** Agentic RAG — LLM agent with tool-use over a hybrid vector store

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Agent Framework | LlamaIndex FunctionAgent | Autonomous query planning and tool orchestration |
| Vector Database | Qdrant | Hybrid search (dense cosine + BM25 sparse) |
| LLM | OpenAI GPT-4o-mini / OpenCode Zen | Query reformulation and answer synthesis |
| Dense Embeddings | OpenAI text-embedding-3-small / HuggingFace bge-small | Document vectorization |
| Sparse Embeddings | fastembed (Qdrant/bm25) | BM25 keyword matching |
| API Framework | FastAPI (async) | REST endpoint + OpenAPI docs |
| Chat UI | Gradio | Browser-based conversational interface |
| Web Scraping | trafilatura + Europe PMC API | Web page and PMC article extraction |
| PDF Parsing | LlamaIndex SimpleDirectoryReader | PDF text extraction |
| Package Manager | uv | Fast Python dependency management |
| Containerization | Docker Compose | App + Qdrant orchestration |
| Settings | pydantic-settings | Typed env-var configuration |

## Key Features

1. **Hybrid search** — combines dense vector similarity (cosine) with BM25 sparse retrieval for better recall
2. **Agentic retrieval** — FunctionAgent can reformulate queries and search multiple times before answering
3. **Source attribution** — every answer includes document/page citations
4. **Multi-source ingestion** — supports PDFs, generic web pages, and PubMed Central articles (via Europe PMC API)
5. **Provider flexibility** — swap between OpenAI and Zen (LLM) or OpenAI and HuggingFace (embeddings) via env vars
6. **Dual interface** — REST API (`POST /query`) and Gradio chat UI (`/chat`)

## Architecture Highlights

```
User → FastAPI /query → FunctionAgent → QueryEngineTool → Qdrant (hybrid) → Response + Sources
         ↑                                                      ↑
       /chat (Gradio)                                   Dense + Sparse vectors
```

- **Ingestion** is a separate CLI step (`ingest.py`) that runs once per data update
- **Query path** is fully async; the agent runs inside the FastAPI lifespan
- **Vector store** persists across restarts via a Docker volume
- **Source capture** uses a monkey-patched tool wrapper to collect `source_nodes` metadata from query results

## Repository Structure

```
├── src/
│   ├── config/       # Settings (env vars) and provider factories
│   ├── core/         # Agent, ingestion pipeline, vector store setup
│   └── api/          # FastAPI routes, Gradio mount, Pydantic models
├── main.py           # Server entry point
├── ingest.py         # CLI ingestion entry point
├── data/             # PDFs and URL list for ingestion
├── tests/            # Unit + e2e tests
├── Dockerfile        # Multi-stage build
└── docker-compose.yml
```

## Key Commands

- **Install:** `uv sync`
- **Dev server:** `uv run python main.py`
- **Ingest:** `uv run python ingest.py`
- **Test:** `uv run pytest tests/`
- **Lint:** `uv run ruff check . && uv run ruff format .`
- **Full stack:** `docker compose up -d`

---

_Generated using BMAD Method `document-project` workflow_
