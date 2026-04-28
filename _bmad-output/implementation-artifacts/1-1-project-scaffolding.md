# Story 1.1: Project Scaffolding

Status: ready-for-dev

## Story

As a developer,
I want a properly structured Python project with all dependencies defined,
so that I have a clean foundation to build features on.

## Acceptance Criteria

1. Project has the 3-layer structure (`src/config/`, `src/core/`, `src/api/`) with `__init__.py` files
2. `pyproject.toml` contains all required dependencies with pinned versions
3. `ruff` is configured in `pyproject.toml` for linting and formatting
4. `.gitignore` excludes `.env`, `__pycache__/`, `.venv/`, `data/pdfs/`
5. `uv sync` installs all dependencies without errors
6. Empty entry point files (`main.py`, `ingest.py`) exist
7. `data/` directory structure exists with placeholder `urls.txt`

## Tasks / Subtasks

- [ ] Task 1: Initialize project with uv (AC: #1, #2, #5)
  - [ ] Run `uv init` in project root
  - [ ] Configure `pyproject.toml` with project metadata (name=info-retrieval-agent, python>=3.10,<4.0)
  - [ ] Add all required dependencies to `pyproject.toml` (see Dev Notes for complete list)
  - [ ] Run `uv sync` and verify all dependencies install without errors
- [ ] Task 2: Create directory structure (AC: #1, #6, #7)
  - [ ] Create `src/__init__.py`
  - [ ] Create `src/config/__init__.py`
  - [ ] Create `src/core/__init__.py`
  - [ ] Create `src/api/__init__.py`
  - [ ] Create empty `main.py` with `if __name__ == "__main__": pass` placeholder
  - [ ] Create empty `ingest.py` with `if __name__ == "__main__": pass` placeholder
  - [ ] Create `data/pdfs/` directory with `.gitkeep`
  - [ ] Create `data/urls.txt` with a comment line explaining format (one URL per line)
- [ ] Task 3: Configure ruff and .gitignore (AC: #3, #4)
  - [ ] Add `[tool.ruff]` section to `pyproject.toml` with line-length=120, target-version="py312"
  - [ ] Add `[tool.ruff.lint]` with select=["E", "F", "I"] (errors, pyflakes, isort)
  - [ ] Add `[tool.ruff.format]` with quote-style="double"
  - [ ] Create `.gitignore` with: `.env`, `__pycache__/`, `.venv/`, `data/pdfs/*.pdf`, `*.pyc`, `.ruff_cache/`
  - [ ] Run `uv run ruff check .` and `uv run ruff format .` to verify ruff works
- [ ] Task 4: Create .env.example (AC: #2)
  - [ ] Create `.env.example` documenting all env vars with comments:
    - `OPENAI_API_KEY=` (required)
    - `LLM_PROVIDER=openai` (optional, default: openai)
    - `LLM_MODEL=gpt-4o-mini` (optional)
    - `EMBED_PROVIDER=openai` (optional, default: openai)
    - `EMBED_MODEL=text-embedding-3-small` (optional)
    - `QDRANT_HOST=localhost` (optional, default: localhost)
    - `QDRANT_PORT=6333` (optional, default: 6333)

## Dev Notes

### Complete Dependency List

From architecture document [Source: architecture.md#Core Architectural Decisions]:

**Core dependencies:**
```
llama-index-core
llama-index-llms-openai
llama-index-embeddings-openai
llama-index-vector-stores-qdrant
qdrant-client
fastapi
uvicorn[standard]
gradio
pydantic-settings
python-dotenv
trafilatura
fastembed
```

**Dev dependencies (optional group):**
```
pytest
pytest-asyncio
httpx
ruff
```

### Project Structure

From architecture document [Source: architecture.md#Project Structure & Boundaries]:

```
info-retrieval-agent/
├── README.md
├── pyproject.toml
├── uv.lock
├── .env.example
├── .env                        # gitignored
├── .gitignore
├── Dockerfile                  # created in Epic 5
├── docker-compose.yml          # created in Epic 5
├── main.py                     # empty placeholder for now
├── ingest.py                   # empty placeholder for now
├── data/
│   ├── pdfs/                   # gitignored PDF content
│   └── urls.txt                # URL list placeholder
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py         # Story 1.2
│   │   └── providers.py        # Story 1.3
│   ├── core/
│   │   ├── __init__.py
│   │   ├── ingestion.py        # Epic 2
│   │   ├── agent.py            # Epic 3
│   │   └── vector_store.py     # Story 2.1
│   └── api/
│       ├── __init__.py
│       ├── app.py              # Epic 4
│       └── models.py           # Epic 4
└── tests/                      # optional for PoC
    └── __init__.py
```

Only create files marked for this story. Other files will be created in their respective stories.

### Architecture Compliance

- **Layer boundaries:** `config/` → `core/` → `api/` (unidirectional imports only) [Source: architecture.md#Implementation Patterns]
- **Naming:** All files `snake_case.py`, PEP 8 throughout [Source: architecture.md#Naming Patterns]
- **Package manager:** `uv` (not pip, not poetry) [Source: architecture.md#Infrastructure & Deployment]
- **Python version:** 3.12 target, >=3.10 compatibility [Source: architecture.md#Infrastructure & Deployment]

### Anti-Patterns to Avoid

- Do NOT create `settings.py`, `providers.py`, or any implementation files — those belong to Stories 1.2 and 1.3
- Do NOT create `Dockerfile` or `docker-compose.yml` — those belong to Epic 5
- Do NOT install the `llama-index` umbrella package — use individual packages for smaller install
- Do NOT use `requirements.txt` — use `pyproject.toml` only

### Testing Notes

This story is primarily scaffolding. Verification is:
- `uv sync` succeeds
- `uv run ruff check .` passes
- `uv run ruff format --check .` passes
- Directory structure exists as specified
- No import errors in empty modules

### References

- [Source: architecture.md#Starter Template & Project Foundation]
- [Source: architecture.md#Core Architectural Decisions → Infrastructure & Deployment]
- [Source: architecture.md#Implementation Patterns & Consistency Rules]
- [Source: architecture.md#Project Structure & Boundaries]
- [Source: prd.md#Non-Functional Requirements → Maintainability]
- [Source: epics.md#Epic 1 → Story 1.1]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

### Change Log
