# Performance Testing Report

**Project:** Info Retrieval Agent  
**Date:** 2026-04-29  
**Method:** Chrome DevTools Protocol + HTTP timing analysis  
**Environment:** Local (macOS, Docker Compose — app + Qdrant)

---

## Executive Summary

The application's frontend and API infrastructure perform excellently. Static pages load in under 10ms, and the server handles concurrent requests efficiently (~417 req/s for simple endpoints). The only notable latency comes from the external LLM API calls during `/query`, which is expected and inherent to the architecture.

**Verdict:** ✅ No actionable performance issues found.

---

## 1. API Response Times

| Endpoint | TTFB | Total | Notes |
|----------|------|-------|-------|
| `GET /health` | <2 ms | 1.5 ms avg | Excellent |
| `GET /chat` (Gradio UI) | 5.0 ms | 5.1 ms | Good — serves 46.5 KB HTML |
| `GET /docs` (Swagger) | 1.5 ms | 1.6 ms | Excellent |
| `POST /query` | 5,476 ms | 5,476 ms | ⚠️ See note below |

### Note on `/query` Response Time

The `/query` endpoint takes 5–8 seconds per request. This is **expected behavior** — the response time is dominated by:
1. Vector similarity search in Qdrant (fast, <100ms)
2. External LLM API call via OpenAI/Zen (slow, 4–7s)
3. Agent may reformulate and call the tool multiple times

This is inherent to the agentic RAG architecture and is **not a bug**. The latency will vary based on:
- LLM provider response time
- Query complexity (may trigger multiple tool calls)
- Network conditions to the LLM API

---

## 2. Frontend Resource Analysis

| Metric | Value | Assessment |
|--------|-------|------------|
| HTML page size | 46.5 KB | ✅ Good |
| Total JS/CSS assets | ~118 KB | ✅ Good (Gradio is lightweight) |
| Number of asset files | 3 | ✅ Minimal requests |
| CSS files | 1 | ✅ Bundled |
| JS files | 3 | ✅ Bundled |

Gradio's asset pipeline efficiently bundles and serves resources. No excessive payload or request waterfall issues.

---

## 3. Concurrent Load Test

### Light endpoints (GET /health × 10 concurrent)

| Metric | Value |
|--------|-------|
| Wall clock | 24 ms |
| Avg latency | 1.3 ms |
| Max latency | 2.0 ms |
| Throughput | ~417 req/s |

**Assessment:** ✅ Excellent. FastAPI + uvicorn handles concurrent lightweight requests with negligible overhead.

### Heavy endpoints (POST /query × 2 concurrent)

| Metric | Value |
|--------|-------|
| Wall clock | 8.2 s |
| Request 1 | 7.6 s |
| Request 2 | 8.2 s |

**Assessment:** Both requests complete in similar time, confirming async handling works correctly — requests are processed in parallel, not serialized. The total wall clock is close to a single request time, not 2×.

---

## 4. Identified Issues

| # | Severity | Issue | Action |
|---|----------|-------|--------|
| 1 | ℹ️ Info | `/query` takes 5–8s due to LLM API latency | Expected — not a bug. Consider streaming responses for better UX in future. |
| 2 | ℹ️ Info | No response caching | Repeated identical queries hit the LLM every time. Consider caching for FAQ-style usage patterns. |
| 3 | ℹ️ Info | No request timeout on `/query` | A stuck LLM call could hold a connection indefinitely. Consider adding `asyncio.wait_for()` with a 60s timeout. |

---

## 5. Recommendations (Non-Blocking)

1. **Streaming responses** — Use Server-Sent Events or WebSocket to stream LLM tokens as they arrive, improving perceived latency in the chat UI.
2. **Request timeout** — Add a 60s timeout on the agent run to prevent hung connections:
   ```python
   import asyncio
   response = await asyncio.wait_for(_agent.run(user_msg=request.question), timeout=60)
   ```
3. **Response caching** — For production, consider an LRU cache keyed on question similarity for common queries.
4. **CDN for static assets** — In production behind a reverse proxy, serve Gradio's static assets with cache headers (`Cache-Control: public, max-age=31536000`).

---

## Conclusion

The application has no performance problems. Infrastructure responses are fast (<5ms), concurrent handling is efficient, and the frontend payload is minimal. The only latency source is the external LLM API, which is architecturally expected and acceptable per product requirements.
