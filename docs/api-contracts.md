# Info Retrieval Agent — API Contracts

**Date:** 2026-04-29

## Base URL

- **Local dev:** `http://localhost:8000`
- **Docker Compose:** `http://localhost:8000`

## Endpoints

### POST /query

Submit a natural-language question and receive a synthesized answer with source citations.

**Request:**

```http
POST /query
Content-Type: application/json

{
  "question": "What are the main topics covered?"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | Yes | Natural-language question to answer from the knowledge base |

**Response (200):**

```json
{
  "answer": "The main topics covered include...",
  "sources": ["document.pdf (p. 5)", "https://example.com/article"]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Synthesized answer from the agent |
| `sources` | string[] | Deduplicated list of source references (file names with page numbers, or URLs) |

**Error Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| 503 | Agent not initialized (startup in progress) | `{"detail": "Agent not initialized"}` |
| 500 | Agent processing error | `{"detail": "Agent error: <message>"}` |

---

### GET /health

Health check endpoint.

**Response (200):**

```json
{
  "status": "healthy"
}
```

---

### /chat (Gradio UI)

Browser-based chat interface mounted via `gr.mount_gradio_app`. Provides a conversational UI backed by the same FunctionAgent.

- **URL:** `http://localhost:8000/chat`
- **Protocol:** Gradio WebSocket + HTTP (handled automatically by Gradio client)
- **Features:** Message history, copy buttons, source links appended to responses

---

### /docs (OpenAPI)

Auto-generated interactive API documentation (Swagger UI).

- **URL:** `http://localhost:8000/docs`

---

## Pydantic Models

```python
class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]

class HealthResponse(BaseModel):
    status: str
```

## Source Attribution Format

Sources are extracted from query result `source_nodes` metadata:

| Metadata Available | Source Format |
|-------------------|--------------|
| `source_url` present | Raw URL string (e.g., `https://example.com/page`) |
| `file_name` + `page_label` | `filename.pdf (p. 3)` |
| `file_name` only | `filename.pdf` |

Sources are deduplicated (preserving order) before returning to the client.

---

_Generated using BMAD Method `document-project` workflow_
