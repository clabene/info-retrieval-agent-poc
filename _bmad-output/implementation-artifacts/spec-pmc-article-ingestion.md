---
title: 'PMC article ingestion via public APIs'
type: 'feature'
created: '2026-04-29'
status: 'done'
route: 'one-shot'
---

## Intent

**Problem:** PMC article URLs (both `/pdf/` and HTML variants) are behind a Cloudflare-style browser check that blocks trafilatura. Ingestion stored only redirect-page boilerplate — 49 docs produced 49 empty chunks with zero usable content.

**Approach:** Detect PMC URLs and fetch full-text via Europe PMC / NCBI E-utilities APIs (which don't require browser JS). Fall back to trafilatura for non-PMC URLs.

## Suggested Review Order

1. [`src/core/ingestion.py:54-68`](../src/core/ingestion.py) — `_PMC_RE` regex and `_extract_pmc_id` — URL detection logic
2. [`src/core/ingestion.py:71-114`](../src/core/ingestion.py) — `_fetch_pmc_text` — two-tier fetch (Europe PMC → NCBI efetch)
3. [`src/core/ingestion.py:117-121`](../src/core/ingestion.py) — `_fetch_generic_url` — trafilatura fallback for non-PMC URLs
4. [`src/core/ingestion.py:148-157`](../src/core/ingestion.py) — routing logic in `load_web_documents` — PMC vs generic dispatch
5. [`data/urls.txt`](../data/urls.txt) — updated URLs (removed `/pdf/` suffixes)
