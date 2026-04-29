# Info Retrieval Agent — Development Guide

**Date:** 2026-04-29

## Prerequisites

- **Python:** ≥ 3.10 (3.12 recommended, matches Dockerfile)
- **uv:** [Install guide](https://docs.astral.sh/uv/getting-started/installation/)
- **Docker & Docker Compose:** For Qdrant (and optionally the full stack)
- **API Key:** One of:
  - `OPENAI_API_KEY` — for both LLM and embeddings (simplest)
  - `ZEN_API_KEY` + HuggingFace embeddings — OpenAI-free setup

## Initial Setup

```bash
# Clone and enter project
cd info-retrieval-agent-docs

# Install all dependencies (including dev)
uv sync

# Copy environment template and configure
cp .env.example .env
# Edit .env with your API keys and preferences
```

## Environment Variables

| Variable | Default | Notes |
|----------|---------|-------|
| `OPENAI_API_KEY` | — | Required if using OpenAI for LLM or embeddings |
| `ZEN_API_KEY` | — | Required if `LLM_PROVIDER=zen` |
| `LLM_PROVIDER` | `openai` | `openai` or `zen` |
| `LLM_MODEL` | `gpt-4o-mini` | Any compatible model name |
| `LLM_API_BASE` | — | Custom API base URL (for Zen or proxies) |
| `EMBED_PROVIDER` | `openai` | `openai` or `huggingface` |
| `EMBED_MODEL` | `text-embedding-3-small` | `BAAI/bge-small-en-v1.5` for HuggingFace |
| `EMBED_DIMS` | `1536` | `384` for bge-small |
| `QDRANT_HOST` | `localhost` | `qdrant` when running in Docker Compose |
| `QDRANT_PORT` | `6333` | Standard Qdrant gRPC port |

## Running Locally

### 1. Start Qdrant

```bash
docker compose up qdrant -d
```

Qdrant will be available at `localhost:6333`. Data persists in a Docker volume (`qdrant_data`).

### 2. Ingest Documents

Place files in `data/pdfs/` and/or add URLs to `data/urls.txt`, then:

```bash
uv run python ingest.py
```

This loads documents, chunks them (512 tokens, 50 overlap), generates embeddings, and stores everything in Qdrant. Run again whenever you add new documents.

### 3. Start the Server

```bash
uv run python main.py
```

Available at:
- API: `http://localhost:8000/query`
- Chat UI: `http://localhost:8000/chat`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Running with Docker Compose (Full Stack)

```bash
docker compose up -d          # Starts both qdrant and app
docker compose exec app uv run python ingest.py  # Ingest from inside container
```

## Testing

```bash
# Unit tests (no infrastructure needed, uses mocks)
uv run pytest tests/ -v --ignore=tests/e2e

# End-to-end tests (requires running Qdrant)
docker compose up qdrant -d
uv run pytest tests/e2e/ -v

# All tests
uv run pytest tests/ -v
```

## Linting & Formatting

```bash
# Check for issues
uv run ruff check .

# Auto-fix
uv run ruff check . --fix

# Format code
uv run ruff format .
```

**Ruff configuration** (from `pyproject.toml`):
- Line length: 120
- Target: Python 3.12
- Rules: E (pycodestyle errors), F (pyflakes), I (isort)
- Quote style: double
- Excluded dirs: `.pi`, `.opencode`, `_bmad`, `_bmad-output`

## Project Conventions

### Import Style
- Absolute imports from project root: `from src.config.settings import get_settings`
- Standard library → third-party → local (enforced by ruff isort)

### Deferred Imports
Heavy dependencies (LlamaIndex pipeline classes) are imported inside functions rather than at module level. This keeps startup validation fast.

### Error Handling
- Configuration errors cause immediate `sys.exit(1)` at startup
- Runtime errors in the agent are caught and returned as HTTP 500 with detail messages
- Ingestion errors for individual URLs/PDFs are logged as warnings; processing continues

### Naming
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

### Testing
- Unit tests mirror source structure: `tests/test_<module>.py`
- E2E tests in `tests/e2e/` require infrastructure (Qdrant)
- Use `pytest-asyncio` for async test functions

## Common Development Tasks

### Adding a new LLM provider

1. Add the provider key validation in `src/config/settings.py`
2. Add a new branch in `get_llm()` in `src/config/providers.py`
3. Add corresponding env vars to `.env.example`

### Adding a new document source

1. Create a `load_<source>_documents()` function in `src/core/ingestion.py`
2. Call it from `ingest.py` and merge with `all_docs`
3. Ensure metadata includes `source_type` for filtering

### Modifying chunk parameters

Edit `run_ingestion_pipeline()` in `src/core/ingestion.py`:
```python
SentenceSplitter(chunk_size=512, chunk_overlap=50)  # adjust here
```

Note: Changing chunk size requires re-ingesting all documents.

---

_Generated using BMAD Method `document-project` workflow_
