# Info Retrieval Agent

A proof-of-concept agentic information-retrieval system that ingests documents (PDFs and web pages), stores them as vector embeddings in Qdrant, and exposes a query API backed by a LlamaIndex FunctionAgent.

The agent autonomously reformulates queries, retrieves relevant context via hybrid search (dense + BM25), evaluates sufficiency, and synthesizes natural-language answers with source attribution.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ Docker Compose                                      │
│                                                     │
│  ┌──────────────┐    ┌───────────────────────────┐  │
│  │   Qdrant     │    │      App Container         │  │
│  │  (persistent │◄──►│                           │  │
│  │   volume)    │    │  FastAPI + Gradio          │  │
│  └──────────────┘    │  LlamaIndex FunctionAgent  │  │
│                      │                           │  │
│                      │  POST /query  → Agent      │  │
│                      │  /chat        → Gradio UI  │  │
│                      │  /health      → Health     │  │
│                      │  /docs        → OpenAPI    │  │
│                      └───────────────────────────┘  │
│                               │                     │
│                               ▼                     │
│                      LLM API (external)             │
│                      OpenAI / OpenCode Zen          │
└─────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Configure

Copy and edit the environment file:

```bash
cp .env.example .env
```

**Minimal setup (OpenAI):**
```env
OPENAI_API_KEY=sk-your-key
```

**OpenAI-free setup (Zen + HuggingFace):**
```env
LLM_PROVIDER=zen
ZEN_API_KEY=your-zen-key
LLM_MODEL=gpt-5.4-mini
EMBED_PROVIDER=huggingface
EMBED_MODEL=BAAI/bge-small-en-v1.5
EMBED_DIMS=384
```

### 2. Add Documents

Place PDF files in `data/pdfs/` and/or add URLs to `data/urls.txt` (one per line):

```
data/
├── pdfs/
│   ├── paper1.pdf
│   └── paper2.pdf
└── urls.txt
```

### 3. Start

```bash
docker compose up -d
```

Wait ~60-90s for first startup (downloads embedding model on first run).

### 4. Ingest Documents

```bash
docker compose exec app uv run python ingest.py
```

This chunks documents, generates embeddings, and stores them in Qdrant. Runs once; data persists across restarts.

### 5. Query

**API:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the main topics covered?"}'
```

**Chat UI:** Open http://localhost:8000/chat

**API Docs:** Open http://localhost:8000/docs

## API

### POST /query

Request:
```json
{"question": "your question here"}
```

Response:
```json
{
  "answer": "synthesized answer...",
  "sources": ["document.pdf (p. 5)", "document.pdf (p. 12)"]
}
```

### GET /health

```json
{"status": "healthy"}
```

## Configuration

All configuration is via environment variables (or `.env` file):

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | When using OpenAI | — | OpenAI API key |
| `ZEN_API_KEY` | When `LLM_PROVIDER=zen` | — | OpenCode Zen API key |
| `LLM_PROVIDER` | No | `openai` | LLM provider: `openai` or `zen` |
| `LLM_MODEL` | No | `gpt-4o-mini` | LLM model name |
| `LLM_API_BASE` | No | — | Custom LLM API base URL |
| `EMBED_PROVIDER` | No | `openai` | Embedding provider: `openai` or `huggingface` |
| `EMBED_MODEL` | No | `text-embedding-3-small` | Embedding model name |
| `EMBED_DIMS` | No | `1536` | Embedding dimensions (384 for bge-small) |
| `QDRANT_HOST` | No | `localhost` | Qdrant hostname |
| `QDRANT_PORT` | No | `6333` | Qdrant port |

## Local Development

```bash
# Install dependencies
uv sync

# Install dev tools
uv pip install pytest ruff

# Start only Qdrant
docker compose up qdrant -d

# Run app locally
uv run python main.py

# Run ingestion locally
uv run python ingest.py

# Lint & format
uv run ruff check .
uv run ruff format .
```

## Testing

The project has three test layers:

### Unit Tests

Fast, fully mocked, no infrastructure required:

```bash
uv run pytest tests/ --ignore=tests/e2e --ignore=tests/playwright
```

Covers: settings validation, provider factories, ingestion logic, agent construction, API routes, source capture.

### Integration / E2E Tests (Python)

Requires **Qdrant running** on `localhost:6333` and a valid **LLM API key** in `.env`:

```bash
uv run pytest tests/e2e/ -v
```

Covers:
- PMC article fetching (Europe PMC + NCBI efetch fallback)
- URL pattern detection and parsing
- Full ingestion pipeline (fetch → chunk → store)
- `/query` endpoint with real agent (answer quality, source attribution)

Tests auto-skip gracefully when infrastructure is unavailable.

### Playwright Tests (Browser UI)

Requires the **app running** on `localhost:8000` (e.g., via `docker compose up`):

```bash
cd tests/playwright
npm install
npx playwright install chromium  # first time only
npx playwright test
```

Covers:
- Page loads correctly (title, input, submit button)
- Chat fills full viewport height
- Submitting a question returns a substantive answer
- Response includes clickable source links (PMC URLs)
- Sources section has a visual separator
- Textarea clears after submission
- Health API endpoint responds

### Running All Tests

```bash
# Unit + E2E (Python)
uv run pytest tests/ -v

# Playwright (separate — needs running app)
cd tests/playwright && npx playwright test
```

## Project Structure

```
├── src/
│   ├── config/
│   │   ├── settings.py      # Pydantic settings (env vars)
│   │   └── providers.py     # LLM, embedding, vector store factories
│   ├── core/
│   │   ├── vector_store.py  # Qdrant collection setup
│   │   ├── ingestion.py     # PDF/web loading, chunking pipeline
│   │   └── agent.py         # FunctionAgent + QueryEngineTool
│   └── api/
│       ├── app.py           # FastAPI routes, Gradio mount
│       └── models.py        # Request/response schemas
├── main.py                  # Server entry point
├── ingest.py                # CLI ingestion entry point
├── Dockerfile
├── docker-compose.yml
└── data/
    ├── pdfs/                # PDF documents for ingestion
    └── urls.txt             # URL list for web ingestion
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent framework | LlamaIndex (FunctionAgent) |
| Vector database | Qdrant (hybrid search: dense + BM25) |
| LLM | OpenAI GPT-4o-mini / OpenCode Zen |
| Embeddings | OpenAI text-embedding-3-small / HuggingFace bge-small |
| API | FastAPI (async) |
| Chat UI | Gradio |
| Package manager | uv |
| Containerization | Docker Compose |
