---
stepsCompleted: [1, 2, 3]
inputDocuments: []
session_topic: 'PoC AI information-retrieval agent backed by vector database'
session_goals: 'Tech stack selection, ingestion pipeline, query API design, agent orchestration, Docker Compose packaging, stretch goals (frontend, live deployment)'
selected_approach: 'ai-recommended'
techniques_used: ['First Principles Thinking', 'Morphological Analysis', 'Constraint Mapping']
ideas_generated: []
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** clabene
**Date:** 2026-04-15

## Session Overview

**Topic:** PoC AI information-retrieval agent backed by vector database (PDFs + web pages), single query-only API, Docker Compose packaging. Bonus: frontend & live deployment.

**Goals:** Generate ideas across tech stack selection, ingestion pipeline design, query API design, agent orchestration patterns, containerization strategy, and stretch goals.

### Session Setup

_Approach selected: AI-Recommended Techniques — facilitator will curate techniques tailored to the session goals._

## Technique Selection

**Approach:** AI-Recommended Techniques
**Analysis Context:** PoC AI info-retrieval agent with focus on tech stack, architecture, and implementation path

**Recommended Techniques:**

1. **First Principles Thinking** (creative) — Strip to fundamentals; define the minimum viable retrieval loop and PoC boundary
2. **Morphological Analysis** (deep) — Systematically map all tech-stack axes and evaluate promising combinations
3. **Constraint Mapping** (deep) — Surface real vs. imagined constraints; stress-test top combos and find the path of least resistance

**AI Rationale:** Technical PoC with many interacting components benefits from grounding in fundamentals first, then systematic enumeration of options, then reality-checking against constraints. This prevents both over-engineering and blind-spot failures.

## Technique Execution Results

### First Principles Thinking

**Interactive Focus:** Decomposing the system into irreducible functional atoms before any tech choices.

**Key Ideas Generated:**

**[Core #1]**: Content must exist in searchable form
_Concept_: Raw documents (PDFs, web pages) must be transformed into something matchable against natural-language questions. The "how" is implementation, not fundamental.
_Novelty_: Separates ingestion concern cleanly from retrieval.

**[Core #2]**: String-in, string-out interface
_Concept_: The system accepts a natural-language string and returns a natural-language string. One endpoint, one input, one output.
_Novelty_: API contract is trivially simple — no structured query language needed.

**[Core #3]**: Semantic matching, not lexical
_Concept_: Matching must be by meaning, not keywords. This is the hard requirement that forces vector/embedding approaches.
_Novelty_: It's a functional necessity, not a tech preference.

**[Core #4]**: Comprehension + synthesis
_Concept_: The system must understand both question and retrieved content, then synthesize — not just return raw chunks.
_Novelty_: Draws a hard line: pure search engine is NOT enough. Generation/reasoning step mandatory.

**[Core #5]**: Query reformulation
_Concept_: The agent should decompose or rephrase user input into better search queries. This is where "agent" earns its name.
_Novelty_: Not just retrieve-then-answer — the agent reasons about *how* to search.

**[Core #6]**: Multi-step agentic retrieval
_Concept_: The agent reasons about what to search, evaluates results, and can issue follow-up queries in a loop. The LLM IS the orchestrator.
_Novelty_: "Agent with a tool" not "RAG pipeline with steps." LLM decides when it has enough.

**[Core #7]**: Stateless sessions
_Concept_: No conversation memory between sessions. Each query is independent. No user state persistence.
_Novelty_: Massively simplifies architecture — no session store, no user DB.

**[Core #8]**: Read-only system
_Concept_: Agent only reads from the knowledge base. No write-back, no side effects. Data flow: ingest (offline) → store → retrieve → respond.
_Novelty_: Clean unidirectional flow, total separation of concerns.

**[Core #9]**: BYOK — Bring Your Own Key
_Concept_: User provides their own LLM API key. System doesn't bundle LLM access. Key passed per-request or via env var.
_Novelty_: Requires provider abstraction layer. No hardcoded OpenAI dependency.

**Open Questions Carried Forward:**
- Ingestion method (manual, API, CLI?) — left undefined
- "I don't know" behavior when KB has no relevant content — left undefined
- Source attribution in responses — left undefined

### Morphological Analysis

**Interactive Focus:** Mapping all axes of tech choice, evaluating combinations, converging on a stack.

**Axes Explored:** Vector DB, Embedding Model, LLM, Agent Framework, API Layer, Ingestion Pipeline, Frontend

**Key Ideas Generated:**

**[Combo #10]**: Combo C+ — Local-First, Cloud-Swappable
_Concept_: Originally designed as Qdrant + Ollama + LlamaIndex + FastAPI + Gradio with LLM slot swappable via env var. Evolved into cloud-default due to memory constraints.
_Novelty_: BYOK as a config toggle, not a code change. Provider abstraction built into the architecture.

**Final Stack Decision:**

| Axis | Choice |
|------|--------|
| Vector DB | Qdrant (Docker, persistent volume) |
| Embeddings | OpenAI text-embedding-3-small |
| LLM | OpenAI GPT-4o-mini |
| Framework | LlamaIndex |
| API | FastAPI |
| Ingestion | LlamaIndex loaders (PDF + web) |
| Frontend | Gradio |
| Containers | 2: Qdrant + App |

### Constraint Mapping

**Interactive Focus:** Stress-testing the chosen stack against real-world constraints.

**[Constraint #11]**: Memory-constrained deployment
_Concept_: Limited RAM. Ollama + Qdrant + App too heavy. Dropped Ollama, use cloud LLM. Docker Compose reduced from 3 to 2 containers.
_Novelty_: Ollama remains a dev-time option, not a deployment requirement.

**[Constraint #12]**: Qdrant needs persistence, not backups
_Concept_: Data must survive container restarts via Docker volume mount. No snapshot/backup strategy needed.
_Novelty_: Simple volumes directive in Docker Compose.

**[Constraint #13]**: Embedding consistency
_Concept_: Switching embedding models invalidates existing vectors — must re-ingest. Pick text-embedding-3-small and stick with it.
_Novelty_: Constraint that's invisible until you hit it.

**[Constraint #14]**: Ingestion is offline/manual
_Concept_: CLI script or Python entrypoint. Takes folder of PDFs + list of URLs, chunks, embeds, pushes to Qdrant. Run once or re-run on content change.
_Novelty_: No upload API for PoC. Simplest possible approach.

**[Constraint #15]**: Single API key covers everything
_Concept_: text-embedding-3-small and gpt-4o-mini share the same OpenAI API key. One credential.
_Novelty_: Clean operational story.

**[Constraint #16]**: Gradio co-hosts with FastAPI
_Concept_: Gradio mounts directly onto FastAPI app. One process, one container, one port. No CORS.
_Novelty_: Eliminates an entire deployment concern.

## Session Summary

### Architecture at a Glance

```
┌─────────────────────────────────────────────────┐
│ Docker Compose                                  │
│                                                 │
│  ┌─────────────┐    ┌────────────────────────┐  │
│  │   Qdrant    │    │       App Container     │  │
│  │ (persistent │◄───│                        │  │
│  │   volume)   │    │  FastAPI + Gradio       │  │
│  └─────────────┘    │  LlamaIndex Agent       │  │
│                     │                        │  │
│                     │  ┌──────────────────┐  │  │
│                     │  │ Query API        │  │  │
│                     │  │ POST /query      │  │  │
│                     │  └──────────────────┘  │  │
│                     │  ┌──────────────────┐  │  │
│                     │  │ Gradio Chat UI   │  │  │
│                     │  └──────────────────┘  │  │
│                     └────────────────────────┘  │
│                            │                    │
│                            ▼                    │
│                     OpenAI API (external)        │
│                     - GPT-4o-mini (LLM)         │
│                     - text-embedding-3-small     │
└─────────────────────────────────────────────────┘

Ingestion: CLI script (offline, LlamaIndex loaders)
BYOK: OPENAI_API_KEY env var, provider-swappable
```

### Core Principles (from First Principles Thinking)
1. String-in, string-out interface
2. Semantic matching (not lexical)
3. Comprehension + synthesis (not raw chunk return)
4. Multi-step agentic retrieval (LLM decides when it has enough)
5. Stateless, read-only, BYOK

### Validated Stack
- **2 Docker containers**: Qdrant (persistent) + App (FastAPI + Gradio + LlamaIndex)
- **1 API key**: OpenAI covers both embeddings and LLM
- **1 CLI script**: Offline ingestion of PDFs + web pages
- **Provider-swappable**: Ollama/Anthropic via config change, not code change

### Key Constraints Surfaced
- Memory-limited: no Ollama in production compose
- Embedding model lock-in: switching requires re-ingestion
- Qdrant persistence via Docker volume (no backups needed)
- Gradio co-hosts with FastAPI (single port)
