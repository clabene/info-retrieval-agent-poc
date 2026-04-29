# Test Automation Summary

_Generated: 2026-04-29_

## Generated Tests

### API E2E Tests (`tests/e2e/test_query_e2e.py`)
- [x] `TestHealthEndpoint::test_health_returns_healthy` — Smoke test
- [x] `TestQueryEndpointE2E::test_hydration_query_returns_answer_and_sources` — Verifies real agent returns answer + PMC sources
- [x] `TestQueryEndpointE2E::test_workout_query_returns_relevant_answer` — Topical query returns relevant content
- [x] `TestQueryEndpointE2E::test_irrelevant_query_admits_no_information` — Out-of-scope query handled gracefully
- [x] `TestQueryEndpointE2E::test_empty_question_returns_422` — Validation error
- [x] `TestQueryEndpointE2E::test_malformed_body_returns_422` — Validation error

### Ingestion E2E Tests (`tests/e2e/test_ingestion_e2e.py`)
- [x] `TestPMCFetch::test_fetch_pmc_text_europe_pmc` — Full text via Europe PMC API
- [x] `TestPMCFetch::test_fetch_pmc_text_falls_back_to_efetch` — Fallback to NCBI efetch
- [x] `TestPMCFetch::test_fetch_pmc_text_returns_none_for_invalid_id` — Invalid PMC ID
- [x] `TestPMCURLDetection::test_detects_standard_pmc_url` — URL regex matching
- [x] `TestPMCURLDetection::test_detects_pmc_pdf_url` — PDF URL variant
- [x] `TestPMCURLDetection::test_detects_old_style_ncbi_url` — Legacy NCBI URL format
- [x] `TestPMCURLDetection::test_returns_none_for_non_pmc_url` — Non-PMC URLs rejected
- [x] `TestIngestionPipeline::test_ingest_single_pmc_article` — Full fetch + parse flow
- [x] `TestIngestionPipeline::test_comments_and_blank_lines_skipped` — URL file parsing

## Coverage

| Area | Tests | Status |
|------|-------|--------|
| API `/query` endpoint (E2E) | 6 | ✅ All pass |
| Ingestion pipeline (E2E) | 9 | ✅ All pass |
| Unit tests (existing) | 46 | ✅ All pass |
| **Total** | **61** | ✅ |

## Requirements

- **Ingestion tests:** Require network access (Europe PMC / NCBI APIs) + Qdrant on localhost:6333
- **Query tests:** Require network + Qdrant + LLM API key (OPENAI_API_KEY or ZEN_API_KEY in env or `.env` file)
- Tests auto-skip gracefully when infrastructure is unavailable

## Run Commands

```bash
# All tests (unit + E2E)
pytest tests/ -x -v

# Unit tests only (no infra needed)
pytest tests/ -x --ignore=tests/e2e/

# E2E only (needs Qdrant + API key)
pytest tests/e2e/ -x -v
```
