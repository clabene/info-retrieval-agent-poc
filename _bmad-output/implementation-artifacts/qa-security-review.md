# Security Review Report

**Project:** Info Retrieval Agent  
**Date:** 2026-04-29  
**Reviewer:** AI Security Audit  
**Scope:** All source code in `src/`, `main.py`, `ingest.py`, `Dockerfile`, `docker-compose.yml`

---

## Executive Summary

The application has a moderate security posture appropriate for a proof-of-concept. Several issues were identified ranging from medium to low severity. No critical vulnerabilities were found, but there are areas that need hardening before production deployment.

**Findings:** 5 issues (0 Critical, 2 High, 2 Medium, 1 Low)

---

## Findings

### [HIGH-1] Server-Side Request Forgery (SSRF) via URL Ingestion

**File:** `src/core/ingestion.py` — `load_web_documents()`, `_fetch_generic_url()`, `_fetch_pmc_text()`  
**CWE:** CWE-918 (Server-Side Request Forgery)

**Description:**  
The ingestion pipeline reads URLs from `data/urls.txt` and fetches them without validation. An attacker who can write to that file (or if the ingestion is ever exposed as an API) could supply internal network URLs (e.g., `http://169.254.169.254/latest/meta-data/` on AWS, `http://localhost:6333` for Qdrant admin) to exfiltrate data from the internal network.

**Current Code:**
```python
def _fetch_generic_url(url: str) -> str | None:
    downloaded = trafilatura.fetch_url(url)  # No URL validation
    ...
```

**Impact:** An attacker could access internal services, cloud metadata endpoints, or the Qdrant database directly.

**Remediation:**
```python
import ipaddress
from urllib.parse import urlparse

BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "[::1]"}
ALLOWED_SCHEMES = {"http", "https"}

def _validate_url(url: str) -> bool:
    """Validate URL is safe to fetch (no internal/metadata endpoints)."""
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        return False
    hostname = parsed.hostname or ""
    if hostname in BLOCKED_HOSTS:
        return False
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except ValueError:
        pass  # Not an IP, that's fine
    return True
```

**Status:** 🔴 Open

---

### [HIGH-2] Uncontrolled Error Disclosure in API Responses

**File:** `src/api/app.py` — `query()` endpoint  
**CWE:** CWE-209 (Generation of Error Message Containing Sensitive Information)

**Description:**  
The `/query` endpoint catches all exceptions and returns the full error message to the client:

```python
except Exception as e:
    logger.error("Agent error: %s", e)
    raise HTTPException(status_code=500, detail=f"Agent error: {e}") from e
```

This can leak internal details: stack traces, API keys in connection strings, internal hostnames, file paths, or Qdrant connection errors revealing infrastructure.

**Impact:** Information disclosure that aids further attacks.

**Remediation:**
```python
except Exception as e:
    logger.error("Agent error: %s", e, exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="An internal error occurred. Please try again later."
    ) from e
```

**Status:** 🔴 Open

---

### [MED-3] No Input Validation / Size Limits on Query Endpoint

**File:** `src/api/models.py` — `QueryRequest`  
**CWE:** CWE-400 (Uncontrolled Resource Consumption)

**Description:**  
The `QueryRequest` model accepts any string with no length limit:

```python
class QueryRequest(BaseModel):
    question: str
```

An attacker could send extremely large payloads (multi-MB strings) to:
- Exhaust memory on the server
- Cause excessive LLM API costs (token billing)
- Trigger timeouts or crashes in the embedding pipeline

**Impact:** Denial of service, cost amplification.

**Remediation:**
```python
from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
```

Also consider adding FastAPI request size middleware:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
# or a custom middleware limiting Content-Length
```

**Status:** 🟡 Open

---

### [MED-4] No Authentication or Rate Limiting

**File:** `src/api/app.py`  
**CWE:** CWE-306 (Missing Authentication for Critical Function), CWE-770 (Allocation of Resources Without Limits)

**Description:**  
The API has no authentication mechanism and no rate limiting. Anyone who can reach port 8000 can:
- Make unlimited queries (incurring LLM API costs)
- Abuse the Gradio chat interface
- Potentially exhaust Qdrant resources

**Impact:** Cost amplification, resource exhaustion, unauthorized access.

**Remediation:**  
For production, add at minimum:
1. **API key authentication** via a header (`X-API-Key`) or Bearer token
2. **Rate limiting** via `slowapi` or similar:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/query")
@limiter.limit("10/minute")
async def query(request: Request, body: QueryRequest):
    ...
```

3. **Network-level restriction** — don't expose port 8000 publicly without a reverse proxy

**Status:** 🟡 Open (acceptable for PoC, required for production)

---

### [LOW-5] Mutable Module-Level State for Source Tracking (Race Condition)

**File:** `src/core/agent.py` — `_last_sources: list[str] = []`  
**CWE:** CWE-362 (Concurrent Execution Using Shared Resource with Improper Synchronization)

**Description:**  
The `_last_sources` list is a module-level global used to pass source information between the tool call and the `/query` endpoint. Under concurrent requests (FastAPI is async), one request could read sources captured by another request:

```python
_last_sources: list[str] = []  # Shared mutable state

# In /query endpoint:
_last_sources.clear()          # Request A clears
response = await _agent.run()  # Request B could append here
sources = list(dict.fromkeys(_last_sources))  # Request A reads B's sources
```

**Impact:** Information leakage between requests (sources from one user's query shown to another).

**Remediation:**  
Use `contextvars` for request-scoped state:

```python
import contextvars

_request_sources: contextvars.ContextVar[list[str]] = contextvars.ContextVar(
    "_request_sources", default=[]
)

# In endpoint:
token = _request_sources.set([])
try:
    response = await _agent.run(user_msg=request.question)
    sources = list(dict.fromkeys(_request_sources.get()))
finally:
    _request_sources.reset(token)
```

**Status:** 🟡 Open

---

## Additional Observations (Informational)

| # | Observation | Notes |
|---|-------------|-------|
| I-1 | **Docker runs as root** | The Dockerfile doesn't create a non-root user. Add `RUN useradd -m app && USER app` |
| I-2 | **No CORS configuration** | FastAPI has no CORS middleware. If the API is consumed by browsers from other origins, add `CORSMiddleware` with an explicit allow-list |
| I-3 | **Secrets in .env file** | API keys are stored in `.env` — ensure `.env` is in `.gitignore` (verify) and use proper secrets management in production |
| I-4 | **No TLS** | The app serves HTTP. In production, use a reverse proxy (nginx/Caddy) with TLS termination |
| I-5 | **XML External Entity (XXE) risk** | `_fetch_pmc_text()` uses `xml.etree.ElementTree` which is safe from XXE by default in Python, but consider using `defusedxml` for defense in depth |
| I-6 | **No Content Security Policy** | The Gradio UI serves without CSP headers. A reverse proxy should add `Content-Security-Policy` headers |

---

## Positive Security Controls Already Present

| Control | Location |
|---------|----------|
| ✅ Pydantic input validation (typed models) | `src/api/models.py` |
| ✅ Settings validation with early fail | `src/config/settings.py` |
| ✅ No SQL — uses vector store (no SQL injection risk) | `src/core/vector_store.py` |
| ✅ No user-supplied file paths in ingestion | `src/core/ingestion.py` |
| ✅ API keys not logged | All modules |
| ✅ Health endpoint doesn't leak system info | `src/api/app.py` |

---

## Remediation Priority

| Priority | Finding | Effort |
|----------|---------|--------|
| 1 | HIGH-2: Error disclosure | Low (10 min) |
| 2 | MED-3: Input size limits | Low (5 min) |
| 3 | HIGH-1: SSRF protection | Medium (30 min) |
| 4 | LOW-5: Race condition fix | Medium (45 min) |
| 5 | MED-4: Auth + rate limiting | High (2-4 hrs) |

---

## Conclusion

The codebase is clean and well-structured with no critical vulnerabilities. The highest-priority fixes (error disclosure and input validation) are trivial to implement. SSRF protection should be added before any deployment where the ingestion pipeline could be influenced by untrusted input. Authentication and rate limiting are essential for any non-local deployment.
