# Project Context for AI Agents

_Critical rules and patterns that AI agents must follow when implementing code in this project. Focuses on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

| Technology | Version / Spec | Notes |
|-----------|---------------|-------|
| Python | ≥ 3.10, target 3.12 | Dockerfile uses `python:3.12-slim` |
| LlamaIndex Core | latest (no pinned version) | Uses `FunctionAgent`, `VectorStoreIndex`, `IngestionPipeline` |
| Qdrant | latest Docker image | Hybrid search: dense (cosine) + sparse (BM25 via fastembed) |
| FastAPI | latest | Async app with lifespan context manager |
| Gradio | latest | Mounted on FastAPI at `/chat` |
| pydantic-settings | latest | `BaseSettings` with `.env` file support |
| uv | latest | Package manager; used in Dockerfile and dev workflow |
| ruff | latest (dev dep) | Linter + formatter, line-length=120, target py312 |
| pytest + pytest-asyncio | latest (dev dep) | Test framework |
| trafilatura | latest | Web page text extraction |
| fastembed | latest | BM25 sparse embeddings for Qdrant |

## Critical Implementation Rules

### Import & Module Conventions

- **Absolute imports only** from project root: `from src.config.settings import get_settings`
- **Deferred heavy imports** — LlamaIndex pipeline classes (`IngestionPipeline`, `SentenceSplitter`, `HuggingFaceEmbedding`) are imported inside functions, NOT at module top level. This keeps startup config validation fast.
- Standard library → third-party → local import order (enforced by ruff `I` rule)

### Configuration Pattern

- All configuration flows through `src/config/settings.py` → `Settings(BaseSettings)`
- `get_settings()` is `@lru_cache`-decorated — single instance, never re-instantiated
- Provider factories in `providers.py` are NOT cached — called fresh each time
- Fail-fast: if config is invalid, `main.py` and `ingest.py` call `sys.exit(1)` immediately

### Provider Abstraction

- LLM and embedding models are created via factory functions (`get_llm()`, `get_embed_model()`, `get_vector_store()`)
- Adding a new provider = add validation in `Settings` + add a branch in the corresponding factory
- `get_vector_store()` creates BOTH sync and async Qdrant clients (required for LlamaIndex compatibility)
- Collection name is hardcoded as `"knowledge_base"` in both `vector_store.py` and `providers.py`

### Agent Architecture

- The agent is built ONCE at FastAPI lifespan startup and held in module-level `_agent` variable
- Source nodes are captured via monkey-patched `call`/`acall` methods on `QueryEngineTool`
- `_last_sources` is a module-level `list[str]` — cleared before each request, read after
- **NOT thread-safe for concurrent requests** — acceptable for PoC, but must be addressed if scaling
- `initial_tool_choice="required"` forces the agent to ALWAYS call the knowledge_base tool before answering
- System prompt explicitly forbids answering from general knowledge

### Ingestion Pipeline

- `ensure_collection()` is idempotent — always call before ingesting
- Chunk parameters: `SentenceSplitter(chunk_size=512, chunk_overlap=50)` — changing requires full re-ingestion
- Sparse vector field name is `"text-sparse-new"` (must match between collection creation and QdrantVectorStore config)
- `enable_hybrid=True` + `fastembed_sparse_model="Qdrant/bm25"` on the vector store handles sparse embedding automatically
- Individual URL/PDF failures are logged and skipped — pipeline continues with remaining documents

### PMC Article Handling

- URLs matching `pmc.ncbi.nlm.nih.gov` or `ncbi.nlm.nih.gov/pmc` are routed to a dedicated API pathway
- Two-tier fallback: Europe PMC full-text XML → NCBI E-utilities efetch
- Generic URLs use trafilatura (standard web scraping)

### API Layer

- Gradio app is mounted via `gr.mount_gradio_app(app, _demo, path="/chat")` — this REPLACES the `app` variable (reassignment)
- The `/query` endpoint is async and awaits `_agent.run()`
- Sources are deduplicated with `list(dict.fromkeys(...))` preserving insertion order

### Testing Rules

- Unit tests in `tests/test_*.py` — no infrastructure required (use mocks)
- E2E tests in `tests/e2e/` — require a running Qdrant instance
- Use `pytest-asyncio` for async test functions
- Test files mirror source structure: `test_agent.py`, `test_ingestion.py`, etc.

### Code Quality & Style

- **Line length:** 120 characters (ruff)
- **Quote style:** double quotes (ruff format)
- **Docstrings:** Google style with Args/Returns sections
- **Type hints:** Used throughout; `list[str]` style (not `List[str]`)
- **Logging:** `logging.getLogger(__name__)` per module; `logging.basicConfig()` in entry points only
- **Excluded from linting:** `.pi`, `.opencode`, `_bmad`, `_bmad-output` directories

### Critical Don't-Miss Rules

- **Never import LlamaIndex at module top level** in `ingestion.py` or `providers.py` (for HuggingFace) — breaks fast config validation
- **Never cache provider instances** — they depend on settings that should be fresh
- **Never modify `COLLECTION_NAME`** without updating both `vector_store.py` AND `providers.py`
- **Never use `_last_sources` across concurrent requests** without adding request-scoped isolation
- **Always call `ensure_collection()` before any write to Qdrant** — it's the only place collection schema is defined
- **Always add `source_type` metadata** to new document loaders — used for payload filtering
- The Gradio `mount_gradio_app` call must be the LAST line that touches `app` — it returns a new ASGI app wrapping FastAPI

---

_Generated using BMAD Method `generate-project-context` workflow_
