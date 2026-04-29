---
project_name: 'info-retrieval-agent'
user_name: 'clabene'
date: '2026-04-29'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow_rules', 'critical_rules']
status: 'complete'
rule_count: 28
optimized_for_llm: true
---

# Project Context for AI Agents

_Critical rules and patterns for implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

| Layer | Technology | Notes |
|-------|-----------|-------|
| Language | Python 3.12 (≥3.10) | Type hints everywhere, `str \| None` union syntax |
| Orchestration | LlamaIndex Core | FunctionAgent workflow, QueryEngineTool |
| LLM | OpenAI (gpt-4o-mini default) | Also supports "zen" provider via api_base swap |
| Embeddings | HuggingFace `BAAI/bge-small-en-v1.5` (384 dims) | Local inference, no API key needed |
| Vector DB | Qdrant (Docker, port 6333) | Hybrid search: dense cosine + BM25 sparse |
| API | FastAPI + Uvicorn | Async, port 8000 |
| Chat UI | Gradio 6.13 (mounted at `/chat`) | `mount_gradio_app` — NOT standalone launch |
| Web scraping | Trafilatura | Only for non-PMC generic URLs |
| Package mgr | uv | `uv.lock` for reproducibility |
| Containers | Docker Compose | `app` (port 8000) + `qdrant` (port 6333) |
| Linting | Ruff | 120 char lines, double quotes, isort |
| Testing | pytest + pytest-asyncio | Mocks for all external services |

---

## Critical Implementation Rules

### Architecture (3-layer)

- **`src/config/`** — Settings (pydantic-settings) + provider factories. NO business logic here.
- **`src/core/`** — Ingestion pipeline, agent construction, vector store setup.
- **`src/api/`** — FastAPI routes + Gradio UI. Thin layer, delegates to core.
- **Entry points:** `main.py` (server), `ingest.py` (CLI ingestion). Both validate config before work.

### Agent & Tool Wrapper Pattern (CRITICAL)

The `FunctionAgent` from LlamaIndex workflows does NOT expose tool call results on its final `AgentOutput`. Source nodes are captured via a **monkey-patched side-effect**:

```python
# src/core/agent.py
_last_sources: list[str] = []  # Module-level collector

# QueryEngineTool.call() and .acall() are monkey-patched to:
# 1. Call the original method
# 2. Extract source_nodes from ToolOutput.raw_output
# 3. Append source URLs/filenames to _last_sources
```

**Rules:**
- Always `_last_sources.clear()` BEFORE calling `agent.run()`
- Read `_last_sources` AFTER `await agent.run()` completes
- `initial_tool_choice="required"` forces the agent to call the tool on first turn (LLM may skip it otherwise)
- This is NOT thread-safe — acceptable for single-process PoC

### Ingestion Pipeline

**PMC articles** (PubMed Central) use a two-tier API fetch, NOT trafilatura:
1. **Europe PMC** `fullTextXML` API — full article text (preferred)
2. **NCBI E-utilities efetch** — fallback (may be abstract-only for restricted publishers)

**Why:** PMC serves a Cloudflare browser-check that blocks all automated HTTP clients (trafilatura, requests, etc.)

**URL detection:** Regex `_PMC_RE` matches both `pmc.ncbi.nlm.nih.gov/articles/PMC{id}/` and `/pdf/` variants.

**Generic URLs** (non-PMC): Use trafilatura as before.

**Chunking:** `SentenceSplitter(chunk_size=512, chunk_overlap=50)` → stored in Qdrant with `bge-small-en-v1.5` dense vectors + BM25 sparse vectors.

### Gradio 6 Mounted App Limitations

When Gradio is mounted via `mount_gradio_app()` (not `launch()`):
- **`css`, `js`, `head` params on `gr.Blocks()` are IGNORED** — they only work with `launch()`
- **Workaround for height:** Set `height="75vh"` directly on `gr.Chatbot()` component
- **`fill_height=True`** on Blocks/ChatInterface has no visible effect when mounted
- The Gradio footer ("Built with Gradio") cannot be hidden via standard params

### Configuration & Provider Switching

- All config via env vars (`.env` file), validated by `pydantic-settings`
- `get_settings()` is `@lru_cache` — call `.cache_clear()` in tests
- Switching embed model invalidates ALL stored vectors — requires full re-ingestion + collection recreation
- `EMBED_DIMS` must match the model (384 for bge-small, 1536 for text-embedding-3-small)

### Vector Store (Qdrant)

- Collection: `knowledge_base` (single collection for all content)
- `ensure_collection()` is idempotent — safe to call multiple times
- Hybrid search: dense vectors (cosine) + sparse BM25 via fastembed
- Payload indexes on: `source_type` (keyword), `file_name` (keyword)
- To reset: delete collection, then re-run `python ingest.py`

---

## Testing Rules

- All external services mocked (OpenAI, Qdrant, HuggingFace)
- Use `monkeypatch.setenv("OPENAI_API_KEY", "sk-test")` in fixtures
- Clear settings cache: `get_settings.cache_clear()` in setup/teardown
- `TestClient(app)` for API tests — agent is mocked via `patch("src.api.app.build_agent")`
- For `_last_sources` tests: directly manipulate the list, no need to mock the agent

---

## Code Quality & Style

- **Ruff:** `line-length = 120`, `select = ["E", "F", "I"]`, double quotes
- **Docstrings:** All public functions have Google-style docstrings with Args/Returns
- **Imports:** stdlib → third-party → local (enforced by ruff isort)
- **Type hints:** All function signatures typed, use `str | None` not `Optional[str]`
- **Error handling:** `logger.warning()` + continue for non-fatal errors (ingestion); `HTTPException` for API errors

---

## Development Workflow

- **Branch:** `main` (no branching strategy for this PoC)
- **Commits:** Conventional commits (`feat:`, `fix:`, `refactor:`)
- **Run tests:** `source .venv/bin/activate && python -m pytest tests/ -x -q`
- **Lint:** `ruff check . && ruff format --check .`
- **Local dev:** `source .venv/bin/activate && python main.py` (needs Qdrant running)
- **Docker:** `docker compose up --build` (builds app, uses qdrant:latest)
- **Ingest data:** `python ingest.py` (reads `data/urls.txt` + `data/pdfs/`)
- **Never auto-push** — human reviews before push

---

## Critical Don't-Miss Rules

1. **Never use trafilatura for PMC URLs** — it only gets browser-check HTML, not article content
2. **Never replace QueryEngineTool with FunctionTool** — FunctionAgent won't invoke FunctionTools reliably
3. **Always set `initial_tool_choice="required"`** — without it, the LLM answers from general knowledge
4. **Qdrant must be running before the app starts** — no graceful degradation on startup
5. **The `data/urls.txt` comment syntax uses `#`** — lines starting with `#` are skipped
6. **`docker compose up --build`** is needed after code changes — the app runs from copied source, not a volume mount
7. **Embedding model change = full re-ingestion** — dimensions are baked into the Qdrant collection schema

---

## Usage Guidelines

**For AI Agents:**
- Read this file before implementing any code in this project
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- If you discover a new pattern or gotcha, flag it for addition

**For Humans:**
- Keep this file lean — only document what agents would otherwise miss
- Update when technology stack or architectural patterns change
- Remove rules that become obvious or outdated

_Last updated: 2026-04-29_
