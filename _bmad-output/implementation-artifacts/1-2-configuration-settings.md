# Story 1.2: Configuration & Settings

Status: review

## Story

As a developer,
I want typed, validated configuration loaded from environment variables,
so that the system fails fast with clear messages when misconfigured.

## Acceptance Criteria

1. A `pydantic-settings` BaseSettings class exists in `src/config/settings.py`
2. When `OPENAI_API_KEY` is present in `.env`, settings load successfully with all defaults resolved
3. Default values: QDRANT_HOST=localhost, QDRANT_PORT=6333, LLM_PROVIDER=openai, LLM_MODEL=gpt-4o-mini, EMBED_MODEL=text-embedding-3-small
4. `.env.example` documents all required and optional environment variables
5. When `OPENAI_API_KEY` is missing or empty, the application raises a clear error message and exits
6. Settings instance is importable from `src/config` package

## Tasks / Subtasks

- [x] Task 1: Create Settings class (AC: #1, #2, #3, #6)
  - [x] Create `src/config/settings.py` with a `Settings` class inheriting from `pydantic_settings.BaseSettings`
  - [x] Define fields: `openai_api_key` (str, required), `llm_provider` (str, default "openai"), `llm_model` (str, default "gpt-4o-mini"), `embed_provider` (str, default "openai"), `embed_model` (str, default "text-embedding-3-small"), `qdrant_host` (str, default "localhost"), `qdrant_port` (int, default 6333)
  - [x] Configure `model_config` with `env_file=".env"` and `env_file_encoding="utf-8"`
  - [x] Add a module-level `get_settings()` function that returns a cached Settings instance (use `@lru_cache`)
  - [x] Export `Settings` and `get_settings` from `src/config/__init__.py`
- [x] Task 2: Validation and fail-fast behavior (AC: #5)
  - [x] Add a `@field_validator("openai_api_key")` that raises ValueError if the key is empty string
  - [x] Verify that missing OPENAI_API_KEY raises a `ValidationError` with a clear message
- [x] Task 3: Write tests (AC: #1-#6)
  - [x] Create `tests/test_settings.py`
  - [x] Test: settings load with valid env vars (mock OPENAI_API_KEY)
  - [x] Test: all defaults are correct when only OPENAI_API_KEY is provided
  - [x] Test: missing OPENAI_API_KEY raises ValidationError
  - [x] Test: empty string OPENAI_API_KEY raises ValidationError
  - [x] Test: custom values override defaults

## Dev Notes

### Architecture Compliance

- File: `src/config/settings.py` [Source: architecture.md#Project Structure & Boundaries]
- Layer: `config/` — imports nothing from `core/` or `api/` [Source: architecture.md#Implementation Patterns]
- Uses `pydantic-settings` (already in dependencies from Story 1.1)
- Environment variable names: UPPER_SNAKE_CASE [Source: architecture.md#Naming Patterns]

### Implementation Pattern

```python
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
    
    openai_api_key: str
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    embed_provider: str = "openai"
    embed_model: str = "text-embedding-3-small"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### Previous Story Intelligence

From Story 1.1:
- `pyproject.toml` already has `pydantic-settings` and `python-dotenv` as dependencies
- `.env.example` already documents all env vars (no changes needed)
- ruff is configured with line-length=120, target py312, isort enabled

### Testing Approach

Use `monkeypatch` or environment variable mocking to test settings without a real `.env` file:

```python
import pytest
from pydantic import ValidationError

def test_settings_loads_with_valid_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    from src.config.settings import Settings
    s = Settings()
    assert s.openai_api_key == "sk-test-key"
```

### Anti-Patterns to Avoid

- Do NOT use `os.getenv()` directly — use pydantic-settings for typed validation
- Do NOT import from `src/core/` or `src/api/` — config layer has no downstream imports
- Do NOT create a global `settings = Settings()` at module level — use `get_settings()` with lru_cache to allow test overrides
- Do NOT hardcode the .env file path — use pydantic-settings default behavior

### References

- [Source: architecture.md#Configuration Management]
- [Source: architecture.md#Implementation Patterns → Process Patterns]
- [Source: prd.md#FR22 — System reads LLM/embedding provider configuration from environment variables]
- [Source: prd.md#FR24 — System fails fast with a clear error message when required configuration is missing]
- [Source: epics.md#Epic 1 → Story 1.2]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4 (via pi coding agent)

### Debug Log References

- pytest/ruff not in main deps — installed via `uv pip install` (dev optional-deps not auto-installed by `uv sync`)

### Completion Notes List

- Settings class with pydantic-settings BaseSettings, 7 fields (1 required, 6 with defaults)
- @field_validator ensures empty API key is rejected
- get_settings() with @lru_cache for singleton pattern
- Exported from src.config package
- 7 tests covering: valid load, defaults, missing key, empty key, overrides, get_settings, package import
- All tests pass, ruff clean

### File List

- src/config/settings.py (new)
- src/config/__init__.py (modified — added exports)
- tests/test_settings.py (new)

### Change Log

- 2026-04-27: Story 1.2 implemented — typed settings with validation, 7 tests passing
