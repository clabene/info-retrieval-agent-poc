---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: 'LlamaIndex Agentic Patterns'
research_goals: 'Overview of how LlamaIndex works, then dive into agentic retrieval patterns for decision-making on info-retrieval agent PoC'
user_name: 'clabene'
date: '2026-04-22'
web_research_enabled: true
source_verification: true
---

# Research Report: Technical

**Date:** 2026-04-22
**Author:** clabene
**Research Type:** Technical

---

## Research Overview

This technical research investigates **LlamaIndex agentic patterns** for building a PoC AI information-retrieval agent backed by Qdrant vector database. The research was conducted on April 22, 2026, covering LlamaIndex v0.14.21 and the validated stack from the brainstorming phase (Qdrant + OpenAI + FastAPI + Gradio). All claims are verified against current official documentation and PyPI package data.

The research spans five areas: core LlamaIndex abstractions and agent types, integration patterns for the full stack, architectural design decisions, and concrete implementation guidance including dependencies, chunking strategies, and a phased roadmap. Key findings and consolidated recommendations are in the Research Synthesis section at the end of this document.

---

## Technical Research Scope Confirmation

**Research Topic:** LlamaIndex Agentic Patterns
**Research Goals:** Overview of how LlamaIndex works, then dive into agentic retrieval patterns for decision-making on info-retrieval agent PoC

**Technical Research Scope:**

- Architecture Analysis - design patterns, frameworks, system architecture
- Implementation Approaches - development methodologies, coding patterns
- Technology Stack - languages, frameworks, tools, platforms
- Integration Patterns - APIs, protocols, interoperability
- Performance Considerations - scalability, optimization, patterns

**Research Methodology:**

- Current web data with rigorous source verification
- Multi-source validation for critical technical claims
- Confidence level framework for uncertain information
- Comprehensive technical coverage with architecture-specific insights

**Scope Confirmed:** 2026-04-22

---

## Technology Stack Analysis

### LlamaIndex: Current State (v0.14.21, April 2026)

LlamaIndex is the leading open-source Python framework for building LLM-powered agentic applications over private data. As of April 21, 2026, the latest release is **v0.14.21** (MIT license).

**Package Architecture:** LlamaIndex uses a modular, namespaced design:
- `llama-index-core` — Core framework (indices, retrievers, query engines, agents, workflows)
- `llama-index-llms-*` — LLM provider integrations (OpenAI, Ollama, Anthropic, etc.)
- `llama-index-embeddings-*` — Embedding provider integrations
- `llama-index-vector-stores-*` — Vector store integrations (Qdrant, etc.)
- `llama-index` — Umbrella "starter" package bundling core + popular integrations

Import convention:
```python
from llama_index.core.xxx import ClassABC       # core module
from llama_index.llms.openai import OpenAI       # integration package
```

_Source: https://pypi.org/project/llama-index/ , https://docs.llamaindex.ai/en/stable/_

### Core Abstractions (The LlamaIndex Mental Model)

LlamaIndex provides a layered set of abstractions, from low-level data handling to high-level agentic orchestration:

#### Data Layer
| Concept | Description |
|---------|-------------|
| **Document** | Container around a data source (PDF, API output, web page, etc.) |
| **Node** | Atomic unit of data — a "chunk" of a Document, with metadata linking it back |
| **Connector / Reader** | Ingests data from sources into Documents and Nodes (hundreds on LlamaHub) |

#### Index & Retrieval Layer
| Concept | Description |
|---------|-------------|
| **Index** | Data structure for querying — typically vector embeddings stored in a vector store |
| **Embedding** | Numerical representation of text meaning; queries are converted to embeddings for similarity matching |
| **Retriever** | Defines how to efficiently find relevant context from an index for a given query |
| **Node Postprocessor** | Transforms, filters, or re-ranks retrieved nodes |
| **Response Synthesizer** | Generates an LLM response from a query + retrieved text chunks |

#### Engine Layer
| Concept | Description |
|---------|-------------|
| **Query Engine** | Stateless question-answering interface over an index (i.e., a RAG pipeline) |
| **Chat Engine** | Conversational interface with multi-turn memory |

#### Agent & Orchestration Layer
| Concept | Description |
|---------|-------------|
| **Agent** | LLM-powered knowledge worker with tools; reasons about what to do, executes tools, loops until done |
| **Workflow** | Event-driven, step-based orchestration for complex multi-step agentic applications |
| **AgentWorkflow** | Pre-built workflow for single or multi-agent systems with handoffs |

_Source: https://docs.llamaindex.ai/en/stable/ , https://docs.llamaindex.ai/en/stable/understanding/rag/_

### Agent Types in LlamaIndex

LlamaIndex provides **three built-in agent implementations**, all subclassing `BaseWorkflowAgent`:

#### 1. FunctionAgent (Recommended for OpenAI/Anthropic)
- Uses the LLM's **native function/tool calling API** to select and invoke tools
- Most reliable with models that have built-in tool support (OpenAI, Anthropic, Gemini)
- Simplest setup — just pass tools and an LLM
- **Best fit for our PoC** given we're using GPT-4o-mini which has strong function calling

#### 2. ReActAgent
- Uses **ReAct prompting** (Reasoning + Acting) — the LLM reasons step-by-step in text, then decides which tool to call
- Works with any capable LLM, including those without native tool-calling
- More verbose in token usage (chain-of-thought reasoning visible)
- Good fallback if switching to Ollama/local models

#### 3. CodeActAgent
- The LLM generates **Python code** to execute tools
- Most flexible but requires code execution sandbox
- Better for complex multi-step computations

```python
from llama_index.core.agent.workflow import FunctionAgent, ReActAgent, CodeActAgent

# FunctionAgent — recommended for OpenAI
agent = FunctionAgent(
    tools=[...],
    llm=OpenAI(model="gpt-4o-mini"),
    system_prompt="You are an information retrieval agent..."
)

# ReActAgent — fallback for local models
agent = ReActAgent(
    tools=[...],
    llm=Ollama(model="llama-3.1:latest"),
    system_prompt="You are an information retrieval agent..."
)
```

_Source: https://docs.llamaindex.ai/en/stable/understanding/agent/ , https://docs.llamaindex.ai/en/stable/api_reference/agent/_

### RAG Pipeline: The 5-Stage Flow

LlamaIndex structures RAG into five stages:

1. **Loading** — Ingest documents via Readers/Connectors (PDF, web, API, DB)
2. **Indexing** — Chunk into Nodes, generate embeddings, store in vector store
3. **Storing** — Persist index + metadata (vector store, docstore)
4. **Querying** — Retrieve relevant nodes, post-process, synthesize response
5. **Evaluation** — Measure accuracy, faithfulness, speed

For our PoC, the flow maps directly:
- **Loading**: `SimpleDirectoryReader` (PDFs) + web reader (URLs)
- **Indexing**: Chunk → embed with `text-embedding-3-small` → push to Qdrant
- **Storing**: Qdrant with Docker volume persistence
- **Querying**: Agent uses a QueryEngineTool wrapping a VectorStoreIndex retriever

_Source: https://docs.llamaindex.ai/en/stable/understanding/rag/_

### Workflows: The Lower-Level Orchestration Primitive

Workflows are LlamaIndex's **event-driven orchestration layer**, replacing older DAG-based approaches:

- **Steps** are async functions decorated with `@step`
- **Events** are Pydantic models that trigger steps
- Steps emit Events → which trigger other Steps → forming arbitrary control flows
- Support loops, branches, concurrent execution, streaming, and state management
- `StartEvent` and `StopEvent` are built-in entry/exit points

Key insight: **Agents (FunctionAgent, ReActAgent) are themselves Workflows**. `AgentWorkflow` is a pre-built Workflow that manages agent execution, tool calling, and multi-agent handoffs.

For our PoC, we likely **don't need custom Workflows** — `FunctionAgent` or `AgentWorkflow` with RAG tools should suffice.

_Source: https://docs.llamaindex.ai/en/stable/understanding/workflows/_

### Multi-Agent Patterns

LlamaIndex supports three multi-agent patterns (overkill for our PoC, but good to know):

1. **AgentWorkflow (swarm)** — Agents hand off to each other; framework manages routing
2. **Orchestrator pattern** — One master agent calls sub-agents as tools
3. **Custom planner (DIY)** — LLM generates a structured plan, your code executes it

_Source: https://docs.llamaindex.ai/en/stable/understanding/agent/multi_agent/_

### Qdrant Integration

LlamaIndex provides `llama-index-vector-stores-qdrant` for Qdrant integration:

```python
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, AsyncQdrantClient

client = QdrantClient(host="localhost", port=6333)
aclient = AsyncQdrantClient(host="localhost", port=6333)

vector_store = QdrantVectorStore(
    collection_name="my_collection",
    client=client,
    aclient=aclient,
)
```

**Hybrid search** is supported by combining dense vectors (OpenAI embeddings) with sparse vectors (BM25 via fastembed):
```python
vector_store = QdrantVectorStore(
    "my_collection",
    client=client,
    aclient=aclient,
    enable_hybrid=True,
    fastembed_sparse_model="Qdrant/bm25",
    batch_size=20,
)
```

This could be a valuable enhancement for our PoC — hybrid search improves keyword-specific queries that pure semantic search might miss.

_Source: https://docs.llamaindex.ai/en/stable/examples/vector_stores/qdrant_hybrid/_

### Putting It Together: Agent + RAG Tool Pattern

The key pattern for our PoC — wrapping a RAG query engine as an agent tool:

```python
from llama_index.core.tools import QueryEngineTool
from llama_index.core.agent.workflow import FunctionAgent

# Build index over ingested documents
index = VectorStoreIndex.from_vector_store(vector_store)

# Create query engine
query_engine = index.as_query_engine(similarity_top_k=5)

# Wrap as agent tool
rag_tool = QueryEngineTool.from_defaults(
    query_engine=query_engine,
    name="knowledge_base",
    description="Search the knowledge base for information from ingested documents.",
)

# Create agent with RAG tool
agent = FunctionAgent(
    tools=[rag_tool],
    llm=OpenAI(model="gpt-4o-mini"),
    system_prompt="You are an information retrieval agent. Use the knowledge_base tool to find relevant information...",
)

# Query
response = await agent.run(user_msg="What is...?")
```

This maps perfectly to our brainstorming decisions: the agent IS the orchestrator, it decides when to search (and can re-search), and it synthesizes the final answer.

_Source: https://docs.llamaindex.ai/en/stable/understanding/putting_it_all_together/agents/_

### Technology Adoption Trends

- LlamaIndex has shifted from a "data framework" to an **"agentic application framework"** — agents and workflows are now front-and-center
- The old `ServiceContext` / `LLMPredictor` patterns are deprecated; use `Settings` global or pass directly
- **Async-first**: All agent/workflow APIs are async (`await agent.run(...)`)
- **Modular installs**: Pick only the integrations you need via `pip install llama-index-*`
- The `Workflow` abstraction replaced earlier graph-based approaches (more flexible, Pythonic)

_Source: https://docs.llamaindex.ai/en/stable/ , https://pypi.org/project/llama-index/_

---

## Integration Patterns Analysis

### Integration Pattern 1: Ingestion Pipeline → Qdrant

The ingestion pipeline is the offline process that loads documents, chunks them, generates embeddings, and pushes vectors into Qdrant.

**Option A: Simple `from_documents` (Quick & Easy)**
```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, AsyncQdrantClient

# Connect to Qdrant
client = QdrantClient(host="localhost", port=6333)
aclient = AsyncQdrantClient(host="localhost", port=6333)
vector_store = QdrantVectorStore(
    collection_name="knowledge_base",
    client=client,
    aclient=aclient,
)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Load and index in one step
documents = SimpleDirectoryReader("./data", required_exts=[".pdf"]).load_data()
index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
    show_progress=True,
)
```
Pros: ~10 lines of code, handles chunking + embedding automatically.
Cons: Less control over chunking/metadata, harder to customize.

**Option B: IngestionPipeline (Recommended for PoC)**
```python
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore

pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512, chunk_overlap=50),
        OpenAIEmbedding(model="text-embedding-3-small"),
    ],
    vector_store=vector_store,
)

# Ingest directly into Qdrant
pipeline.run(documents=documents, show_progress=True)

# Later, create index from existing vector store
index = VectorStoreIndex.from_vector_store(vector_store)
```
Pros: Full control over chunking, metadata extraction, caching. Can persist pipeline cache to avoid re-processing unchanged documents. Supports parallel processing (`num_workers=4`).
Cons: Slightly more code.

**Recommendation:** Option B — the `IngestionPipeline` gives us control over chunk size (important for retrieval quality) and built-in caching.

_Source: https://docs.llamaindex.ai/en/stable/module_guides/loading/ingestion_pipeline/root/_

### Integration Pattern 2: Document Loading (PDFs + Web Pages)

**PDFs:** `SimpleDirectoryReader` handles PDFs natively — just point it at a folder:
```python
from llama_index.core import SimpleDirectoryReader

# Load all PDFs from a directory
docs = SimpleDirectoryReader(
    input_dir="./data/pdfs",
    required_exts=[".pdf"],
    recursive=True,
).load_data()
```
Automatically extracts: `file_path`, `file_name`, `file_type`, `file_size`, `creation_date`, `last_modified_date`. Custom metadata functions can be passed via `file_metadata=fn`.

**Web Pages:** Use `llama-index-readers-web` (v0.6.0):
```python
# pip install llama-index-readers-web
from llama_index.readers.web import SimpleWebPageReader
# or for better extraction:
from llama_index.readers.web import TrafilaturaWebReader

urls = ["https://example.com/page1", "https://example.com/page2"]
docs = TrafilaturaWebReader().load_data(urls)
```
`TrafilaturaWebReader` uses the trafilatura library for clean content extraction (strips nav, ads, etc.) — better than raw HTML parsing.

**Combined ingestion script pattern:**
```python
# Load from multiple sources
pdf_docs = SimpleDirectoryReader("./data/pdfs", required_exts=[".pdf"]).load_data()
web_docs = TrafilaturaWebReader().load_data(url_list)
all_docs = pdf_docs + web_docs

# Run through pipeline
pipeline.run(documents=all_docs)
```

_Source: https://docs.llamaindex.ai/en/stable/module_guides/loading/simpledirectoryreader/ , https://pypi.org/project/llama-index-readers-web/_

### Integration Pattern 3: Provider Abstraction (BYOK / Swappable LLM+Embeddings)

LlamaIndex provides two mechanisms for configuring LLM and embedding providers:

**Global Settings (singleton):**
```python
from llama_index.core import Settings
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding

Settings.llm = OpenAI(model="gpt-4o-mini")
Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.chunk_size = 512
Settings.chunk_overlap = 50
```

**Local overrides (per-component):**
```python
# Override at query time
query_engine = index.as_query_engine(llm=my_other_llm)
agent = FunctionAgent(tools=[...], llm=my_other_llm)
```

**Provider swapping via environment config:**
```python
import os

def get_llm():
    provider = os.getenv("LLM_PROVIDER", "openai")
    if provider == "openai":
        from llama_index.llms.openai import OpenAI
        return OpenAI(model=os.getenv("LLM_MODEL", "gpt-4o-mini"))
    elif provider == "ollama":
        from llama_index.llms.ollama import Ollama
        return Ollama(model=os.getenv("LLM_MODEL", "llama3.1:latest"))
    elif provider == "anthropic":
        from llama_index.llms.anthropic import Anthropic
        return Anthropic(model=os.getenv("LLM_MODEL", "claude-sonnet-4-20250514"))

def get_embed_model():
    provider = os.getenv("EMBED_PROVIDER", "openai")
    if provider == "openai":
        from llama_index.embeddings.openai import OpenAIEmbedding
        return OpenAIEmbedding(model=os.getenv("EMBED_MODEL", "text-embedding-3-small"))
    elif provider == "huggingface":
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
        return HuggingFaceEmbedding(model_name=os.getenv("EMBED_MODEL", "BAAI/bge-small-en-v1.5"))
```

**Key constraint (from brainstorming):** Switching embedding models invalidates existing vectors — requires full re-ingestion. LLM can be swapped freely.

**Note on tokenizer:** When switching LLMs, update the tokenizer to match:
```python
import tiktoken
Settings.tokenizer = tiktoken.encoding_for_model("gpt-4o-mini").encode
```

_Source: https://docs.llamaindex.ai/en/stable/module_guides/supporting_modules/settings/ , https://docs.llamaindex.ai/en/stable/module_guides/models/llms/_

### Integration Pattern 4: Agent → Query Engine as Tool

This is the central integration for our PoC — the agent uses a RAG query engine as its primary tool:

```python
from llama_index.core.tools import QueryEngineTool
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core import VectorStoreIndex

# Build index from existing Qdrant collection
index = VectorStoreIndex.from_vector_store(vector_store)

# Create query engine with tuned retrieval
query_engine = index.as_query_engine(
    similarity_top_k=5,
    # For hybrid search:
    # sparse_top_k=10,
    # vector_store_query_mode="hybrid",
)

# Wrap as agent tool
rag_tool = QueryEngineTool.from_defaults(
    query_engine=query_engine,
    name="knowledge_base",
    description=(
        "Search the knowledge base for information from ingested documents. "
        "Use this tool to find answers to questions about the indexed content. "
        "Input should be a natural language question or search query."
    ),
)

# Create the agent
agent = FunctionAgent(
    tools=[rag_tool],
    llm=OpenAI(model="gpt-4o-mini"),
    system_prompt=(
        "You are an information retrieval agent. Use the knowledge_base tool to find "
        "relevant information from the indexed documents. If you cannot find a relevant "
        "answer, say so clearly. Always cite which documents your answer is based on."
    ),
)

# Run (async)
response = await agent.run(user_msg="What is...?")
```

The agent autonomously decides:
1. Whether to call the tool (or answer from general knowledge)
2. How to formulate the query to the tool
3. Whether the retrieved context is sufficient, or if it needs to re-query
4. How to synthesize the final answer from retrieved chunks

This maps directly to brainstorming Core #5 (query reformulation) and Core #6 (multi-step agentic retrieval).

_Source: https://docs.llamaindex.ai/en/stable/understanding/putting_it_all_together/agents/ , https://docs.llamaindex.ai/en/stable/understanding/agent/_

### Integration Pattern 5: FastAPI + Gradio Co-hosting

Gradio can mount directly onto a FastAPI app — single process, single port, no CORS:

```python
import gradio as gr
from fastapi import FastAPI
import uvicorn

app = FastAPI()

# API endpoint
@app.post("/query")
async def query(request: QueryRequest):
    response = await agent.run(user_msg=request.question)
    return {"answer": str(response)}

# Gradio chat UI
def chat_fn(message, history):
    import asyncio
    response = asyncio.run(agent.run(user_msg=message))
    return str(response)

demo = gr.ChatInterface(fn=chat_fn, title="Knowledge Base Agent")

# Mount Gradio onto FastAPI
app = gr.mount_gradio_app(app, demo, path="/chat")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

This gives:
- `POST /query` — programmatic API
- `/chat` — Gradio web UI
- Single container, single port (8000)

**Note:** Since LlamaIndex agents are async-first, and FastAPI is natively async, they integrate cleanly. The Gradio chat function needs an async bridge if using `gr.ChatInterface` (which is sync by default), or use Gradio's async support.

_Source: https://www.gradio.app/guides/sharing-your-app#mounting-within-another-fast-api-app_

### Integration Pattern 6: Qdrant Hybrid Search (Optional Enhancement)

Hybrid search combines dense vectors (semantic) with sparse vectors (keyword/BM25) for better retrieval:

```python
vector_store = QdrantVectorStore(
    collection_name="knowledge_base",
    client=client,
    aclient=aclient,
    enable_hybrid=True,
    fastembed_sparse_model="Qdrant/bm25",
    batch_size=20,
)

# At query time:
query_engine = index.as_query_engine(
    similarity_top_k=5,       # final results after fusion
    sparse_top_k=12,          # candidates from each vector space
    vector_store_query_mode="hybrid",
)
```

Requires: `pip install fastembed` (runs locally, no API calls for sparse vectors).

**Trade-off:** Better retrieval quality (especially for keyword-specific queries) vs. slightly more complexity and local compute for BM25 encoding.

_Source: https://docs.llamaindex.ai/en/stable/examples/vector_stores/qdrant_hybrid/_

---

## Architectural Patterns and Design

### System Architecture: Single-Agent RAG Pattern

Our PoC follows a clean **single-agent RAG** architecture. Based on the research, here's the refined system design:

```
┌─────────────────────────────────────────────────────────────┐
│ Docker Compose                                              │
│                                                             │
│  ┌──────────────┐    ┌────────────────────────────────────┐ │
│  │   Qdrant     │    │          App Container              │ │
│  │  :6333       │◄──►│                                    │ │
│  │  (persistent │    │  ┌──────────────────────────────┐  │ │
│  │   volume)    │    │  │     FastAPI Application       │  │ │
│  └──────────────┘    │  │                              │  │ │
│                      │  │  POST /query ─► Agent.run()  │  │ │
│                      │  │  /chat ──────► Gradio UI     │  │ │
│                      │  └──────────┬───────────────────┘  │ │
│                      │             │                      │ │
│                      │  ┌──────────▼───────────────────┐  │ │
│                      │  │     FunctionAgent             │  │ │
│                      │  │  ┌─────────────────────────┐  │  │ │
│                      │  │  │ QueryEngineTool         │  │  │ │
│                      │  │  │ (VectorStoreIndex)      │  │  │ │
│                      │  │  └─────────────────────────┘  │  │ │
│                      │  └──────────────────────────────┘  │ │
│                      └────────────────────────────────────┘ │
│                               │                             │
│                               ▼                             │
│                      OpenAI API (external)                  │
│                      • GPT-4o-mini (agent LLM)              │
│                      • text-embedding-3-small (retrieval)   │
└─────────────────────────────────────────────────────────────┘
```

This is a **modular monolith** — single container, single process, clear internal boundaries. Appropriate for a PoC that can be decomposed later if needed.

### Application Layer Design

Based on LlamaIndex patterns and our PoC requirements, the application has three clear layers:

**1. Configuration Layer** — Provider factories, settings, environment loading
```
config/
  settings.py       # Load env vars, create Settings
  providers.py      # get_llm(), get_embed_model() factory functions
```

**2. Core Layer** — Ingestion pipeline and agent setup
```
core/
  ingestion.py      # IngestionPipeline: load docs, chunk, embed, push to Qdrant
  agent.py          # Build FunctionAgent with QueryEngineTool over VectorStoreIndex
  vector_store.py   # Qdrant client setup and VectorStoreIndex creation
```

**3. API Layer** — FastAPI endpoints and Gradio UI
```
api/
  app.py            # FastAPI app, POST /query, Gradio mount
  models.py         # Pydantic request/response schemas
```

**Entry points:**
```
main.py             # uvicorn app startup
ingest.py           # CLI script for offline ingestion
```

This maps to a clean project structure:
```
info-retrieval-agent/
├── src/
│   ├── config/
│   │   ├── settings.py
│   │   └── providers.py
│   ├── core/
│   │   ├── ingestion.py
│   │   ├── agent.py
│   │   └── vector_store.py
│   └── api/
│       ├── app.py
│       └── models.py
├── ingest.py
├── main.py
├── data/                # PDFs + URL lists for ingestion
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── .env.example
```

### Async-First Design

LlamaIndex agents and workflows are **async-first**. All agent operations use `await`:

```python
response = await agent.run(user_msg="What is...?")
```

FastAPI is natively async, so this integrates cleanly:
```python
@app.post("/query")
async def query(request: QueryRequest):
    response = await agent.run(user_msg=request.question)
    return {"answer": str(response)}
```

**Important:** The Qdrant client also provides `AsyncQdrantClient` — always initialize both sync and async clients for maximum compatibility.

_Source: https://docs.llamaindex.ai/en/stable/understanding/agent/ , https://docs.llamaindex.ai/en/stable/understanding/putting_it_all_together/apps/_

### Streaming Architecture

For better UX, the agent can stream responses token-by-token:

```python
from llama_index.core.agent.workflow import AgentStream

# Don't await — get the handler
handler = agent.run(user_msg="What is...?")

# Stream events
async for event in handler.stream_events():
    if isinstance(event, AgentStream):
        yield event.delta  # stream to client
```

**Available stream events:**
- `AgentStream` — token-by-token LLM output
- `AgentInput` — full input message
- `AgentOutput` — complete response
- `ToolCall` — which tool was called and with what arguments
- `ToolCallResult` — result of the tool call

This can be exposed via **Server-Sent Events (SSE)** in FastAPI:
```python
from fastapi.responses import StreamingResponse

@app.post("/query/stream")
async def query_stream(request: QueryRequest):
    async def event_generator():
        handler = agent.run(user_msg=request.question)
        async for event in handler.stream_events():
            if isinstance(event, AgentStream):
                yield f"data: {event.delta}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

**Decision:** Streaming is a nice-to-have for the PoC. The non-streaming `await agent.run()` works fine for MVP and is simpler.

_Source: https://docs.llamaindex.ai/en/stable/understanding/agent/streaming/_

### State Management

Per our brainstorming decision (Core #7): **stateless sessions**. Each query is independent.

However, LlamaIndex provides `Context` for stateful agents if needed later:
```python
from llama_index.core.workflow import Context

ctx = Context(agent)
response1 = await agent.run(user_msg="...", ctx=ctx)
response2 = await agent.run(user_msg="follow up...", ctx=ctx)  # remembers previous
```

Context is serializable (`ctx.to_dict()` / `Context.from_dict()`) for persistence. This is a clean upgrade path if we want to add chat memory later.

For our PoC: **no Context needed** — each `/query` call creates a fresh agent run.

_Source: https://docs.llamaindex.ai/en/stable/understanding/agent/state/_

### Error Handling Strategy

Key failure modes for an LLM agent system:

| Failure | Handling |
|---------|----------|
| OpenAI API down/rate-limited | Retry with backoff; LlamaIndex LLMs have built-in retry. Return 503 to client. |
| Qdrant unreachable | Health check endpoint; fail fast with clear error message. |
| No relevant documents found | Agent system prompt instructs: "If you cannot find relevant information, say so clearly." |
| Embedding dimension mismatch | Prevent at ingestion time; validate collection exists with correct dimensions. |
| Timeout on long agent loops | Set `timeout` parameter on Workflow/Agent (e.g., 60s). FastAPI request timeout. |
| Invalid API key | Validate on startup; return 401 with clear message. |

```python
# Health check endpoint
@app.get("/health")
async def health():
    try:
        # Check Qdrant
        client.get_collections()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Observability (Stretch Goal)

LlamaIndex supports one-click observability via OpenTelemetry:
```python
from llama_index.observability.otel import LlamaIndexOpenTelemetry
instrumentor = LlamaIndexOpenTelemetry()
instrumentor.start_registering()
```

This traces all LLM calls, embeddings, retrievals, and agent steps. Not needed for MVP but a clean add-on.

_Source: https://docs.llamaindex.ai/en/stable/module_guides/observability/_

### Docker Compose Architecture

```yaml
version: "3.8"
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - qdrant
    environment:
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
    restart: unless-stopped

volumes:
  qdrant_data:
```

**2 containers**, shared Docker network, Qdrant data persisted via named volume. App references Qdrant by service name (`qdrant:6333`).

_Source: Brainstorming session architecture decisions_

### Key Architectural Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Modular monolith (single container) | PoC simplicity; clear internal boundaries |
| Agent type | `FunctionAgent` | Native OpenAI tool calling; cleanest for GPT-4o-mini |
| Concurrency | Async-first (FastAPI + async LlamaIndex) | Natural fit; no thread management |
| State | Stateless per request | Brainstorming Core #7; simplest possible |
| Streaming | Optional (SSE endpoint) | Nice UX but not MVP-critical |
| Observability | OpenTelemetry (stretch goal) | One-click LlamaIndex integration |
| Error handling | Health checks + agent timeout + clear "I don't know" | Graceful degradation |

---

## Implementation Approaches and Technology Adoption

### Concrete Dependency List

**Core dependencies** (minimal install):
```toml
[project]
name = "info-retrieval-agent"
requires-python = ">=3.10,<4.0"
dependencies = [
    # LlamaIndex core + integrations
    "llama-index-core",
    "llama-index-llms-openai",
    "llama-index-embeddings-openai",
    "llama-index-vector-stores-qdrant",      # v0.10.0
    "llama-index-readers-web",               # v0.6.0 (TrafilaturaWebReader)

    # Vector DB client
    "qdrant-client",

    # API + UI
    "fastapi",
    "uvicorn[standard]",
    "gradio",

    # Config
    "python-dotenv",
    "pydantic",
    "pydantic-settings",
]

[project.optional-dependencies]
# Provider swapping
ollama = ["llama-index-llms-ollama"]
anthropic = ["llama-index-llms-anthropic"]

# Hybrid search
hybrid = ["fastembed"]

# Development
dev = ["pytest", "pytest-asyncio", "httpx", "ruff"]
```

**Package versions (as of April 2026):**
| Package | Version | Notes |
|---------|---------|-------|
| `llama-index` (umbrella) | 0.14.21 | Or install individual packages |
| `llama-index-vector-stores-qdrant` | 0.10.0 | MIT license |
| `llama-index-readers-web` | 0.6.0 | GPL-3.0 (⚠️ check license compatibility) |
| `text-embedding-3-small` | — | 1536 dimensions, max 8192 tokens input, ~62,500 pages/$1 |
| `gpt-4o-mini` | — | Function calling support, cost-effective |
| Python | ≥3.10, <4.0 | Required by all LlamaIndex packages |

_Source: https://pypi.org/project/llama-index/ , https://pypi.org/project/llama-index-vector-stores-qdrant/ , https://pypi.org/project/llama-index-readers-web/ , https://platform.openai.com/docs/guides/embeddings_

### Chunking Strategy

Chunking is one of the most impactful decisions for retrieval quality. LlamaIndex provides several node parsers:

| Splitter | How it works | Best for |
|----------|-------------|----------|
| `SentenceSplitter` | Splits by sentence boundaries, respects chunk_size | General purpose (recommended default) |
| `TokenTextSplitter` | Splits by token count | When exact token control matters |
| `SemanticSplitterNodeParser` | Adaptive breakpoints using embedding similarity | Higher quality, more expensive |
| `SentenceWindowNodeParser` | Per-sentence embeddings + window context for synthesis | Fine-grained retrieval + rich synthesis |
| `MarkdownNodeParser` | Splits by markdown structure (headers) | Structured markdown documents |
| `HTMLNodeParser` | Splits by HTML tags | Web page content |

**Recommended for PoC:**
```python
from llama_index.core.node_parser import SentenceSplitter

splitter = SentenceSplitter(
    chunk_size=512,       # tokens per chunk
    chunk_overlap=50,     # overlap for context continuity
)
```

**Why 512 tokens?**
- Small enough for precise retrieval (avoids "lost in the middle" with giant chunks)
- Large enough to carry meaningful context
- Fits well within `text-embedding-3-small`'s 8192 token input limit
- LlamaIndex default recommendation for most use cases

**Production enhancement:** Consider `SentenceWindowNodeParser` (embed single sentences, but pass surrounding window to LLM for synthesis) — gives best-of-both-worlds for precision + context.

_Source: https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/modules/ , https://docs.llamaindex.ai/en/stable/optimizing/production_rag/_

### Production RAG Optimization Techniques

LlamaIndex documents several techniques for moving from prototype to production RAG:

1. **Decouple retrieval chunks from synthesis chunks** — Embed summaries or sentences, but pass larger context to LLM. Use `SentenceWindowNodeParser` + `MetadataReplacementNodePostProcessor`.

2. **Structured retrieval for larger document sets** — When you have many PDFs, use metadata filters + auto-retrieval, or document summary hierarchies.

3. **Dynamic retrieval based on task** — Use routers to pick the right retrieval strategy (QA vs. summarization vs. comparison).

4. **Optimize embeddings** — Fine-tune embedding models on your corpus for better relevance.

**For our PoC:** Start with basic `SentenceSplitter(512, 50)` + `similarity_top_k=5`. This is the simplest working setup. Optimize later based on evaluation results.

_Source: https://docs.llamaindex.ai/en/stable/optimizing/production_rag/_

### System Prompt Design

The agent's system prompt is critical for controlling behavior. Based on our brainstorming principles:

```python
SYSTEM_PROMPT = """\
You are an information retrieval agent. Your job is to answer questions 
using ONLY the knowledge base tool provided to you.

Rules:
1. ALWAYS use the knowledge_base tool to search for relevant information 
   before answering.
2. If the tool returns relevant information, synthesize a clear answer 
   and cite which documents your answer is based on.
3. If the tool returns no relevant information, say clearly: 
   "I could not find information about this in the knowledge base."
4. Do NOT make up information or answer from your general knowledge.
5. If the initial search doesn't fully answer the question, reformulate 
   your query and search again.
6. Keep answers concise but comprehensive.
"""
```

Key design decisions:
- **Tool-first**: Forces agent to search before answering (Core #3: comprehension + synthesis)
- **Honest "I don't know"**: Prevents hallucination from general knowledge
- **Re-query permission**: Enables multi-step agentic retrieval (Core #6)
- **Source citation**: Traceability to source documents

### Testing Strategy

LlamaIndex provides built-in evaluation modules. For our PoC:

**1. Retrieval evaluation** — Are the right chunks being retrieved?
```python
from llama_index.core.evaluation import RetrieverEvaluator

# Measures: hit_rate, MRR (mean reciprocal rank)
evaluator = RetrieverEvaluator.from_metric_names(["hit_rate", "mrr"])
results = await evaluator.aevaluate(query="...", expected_ids=["..."])
```

**2. Response evaluation** — Is the answer faithful and relevant?
```python
from llama_index.core.evaluation import FaithfulnessEvaluator, RelevancyEvaluator

# Faithfulness: Is the answer grounded in retrieved context? (no hallucination)
faithfulness_evaluator = FaithfulnessEvaluator()

# Relevancy: Is the answer relevant to the query?
relevancy_evaluator = RelevancyEvaluator()
```

**3. API-level testing:**
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_query_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/query", json={"question": "What is...?"})
        assert response.status_code == 200
        assert "answer" in response.json()
```

_Source: https://docs.llamaindex.ai/en/stable/module_guides/evaluating/_

### Implementation Roadmap

**Phase 1: Foundation (MVP)**
1. Set up project structure + `pyproject.toml`
2. Implement config layer (`settings.py`, `providers.py`)
3. Implement Qdrant vector store setup (`vector_store.py`)
4. Build ingestion pipeline (`ingestion.py`) + CLI script (`ingest.py`)
5. Build agent with QueryEngineTool (`agent.py`)
6. Create FastAPI endpoints (`POST /query`, `/health`)
7. Add Gradio chat UI mounted on FastAPI
8. Docker Compose (Qdrant + App)
9. Basic tests

**Phase 2: Polish**
10. Streaming SSE endpoint (`POST /query/stream`)
11. Source citation in responses
12. Hybrid search (BM25 + dense)
13. Evaluation pipeline (faithfulness + relevancy)

**Phase 3: Stretch**
14. Provider swapping (Ollama, Anthropic)
15. OpenTelemetry observability
16. Production deployment

### Risk Assessment and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| `llama-index-readers-web` is GPL-3.0 | License contamination | Use `SimpleWebPageReader` (MIT) instead, or isolate in separate process |
| LlamaIndex breaking API changes | Rework needed | Pin versions in `pyproject.toml`; LlamaIndex v0.14.x is stable |
| Poor retrieval quality on PDFs | Bad user experience | Test with real docs early; tune chunk_size and top_k |
| OpenAI rate limits under load | Timeouts, errors | Implement retry + backoff; consider caching frequent queries |
| Qdrant cold start after restart | No data available | Named Docker volume persists data; validate on startup |
| Agent loops indefinitely | Hung requests | Set `timeout=60` on agent; FastAPI request timeout |

---

## Research Synthesis

### Executive Summary

This research confirms that **LlamaIndex v0.14.21 is a strong fit** for our PoC information-retrieval agent. The framework has evolved from a "data framework" into a full **agentic application framework**, and its abstractions align almost 1:1 with our brainstorming architecture.

The core implementation pattern is remarkably simple: ingest documents via `IngestionPipeline` → store in Qdrant → wrap as `QueryEngineTool` → give to `FunctionAgent` → expose via FastAPI. The agent autonomously decides when to search, how to reformulate queries, and when it has enough context to answer — fulfilling our brainstorming principles of multi-step agentic retrieval and LLM-as-orchestrator.

The validated stack (Qdrant + OpenAI GPT-4o-mini + text-embedding-3-small + LlamaIndex + FastAPI + Gradio) has first-class integration support across all components, with async-first design throughout and a clean provider-swapping story via factory functions.

### Key Findings

1. **`FunctionAgent` is the right agent type** for GPT-4o-mini — uses native OpenAI tool calling, simplest code, most reliable. `ReActAgent` is a drop-in fallback for Ollama/local models.

2. **`IngestionPipeline` over `from_documents`** — gives control over chunking, supports caching (avoid re-processing), parallel processing, and pipes directly into Qdrant.

3. **`SentenceSplitter(512, 50)` is the right starting point** for chunking. Production upgrade path: `SentenceWindowNodeParser` for finer-grained retrieval with richer synthesis context.

4. **Hybrid search (dense + BM25) is a low-effort enhancement** — `enable_hybrid=True` + `fastembed` adds keyword matching for queries that pure semantic search misses.

5. **Async-first architecture is mandatory** — LlamaIndex agents are `await`-based; FastAPI is natively async; Qdrant provides `AsyncQdrantClient`. Everything aligns.

6. **Gradio co-hosts cleanly on FastAPI** — `gr.mount_gradio_app()`, single process, single port, no CORS.

7. **Stateless design confirmed** — no `Context` persistence needed for MVP. Clean upgrade path to stateful chat via serializable `Context` if needed later.

8. **Streaming is a nice-to-have** — `AgentStream` events over SSE give real-time UX. Not MVP-critical but architecturally clean to add.

### Consolidated Technology Decisions

| Decision | Choice | Confidence |
|----------|--------|------------|
| LlamaIndex version | v0.14.21 (modular install) | ✅ High |
| Agent type | `FunctionAgent` | ✅ High |
| Agent fallback | `ReActAgent` (for Ollama) | ✅ High |
| Ingestion | `IngestionPipeline` + `SentenceSplitter(512, 50)` | ✅ High |
| PDF loading | `SimpleDirectoryReader` | ✅ High |
| Web loading | `TrafilaturaWebReader` (check GPL-3.0 license) | 🟡 Medium |
| Vector store | Qdrant with `QdrantVectorStore` | ✅ High |
| Embeddings | `text-embedding-3-small` (1536 dims) | ✅ High |
| LLM | `gpt-4o-mini` via `OpenAI` | ✅ High |
| API framework | FastAPI (async) | ✅ High |
| UI | Gradio mounted on FastAPI | ✅ High |
| Hybrid search | Optional (`enable_hybrid=True` + fastembed) | 🟡 Medium |
| Streaming | Optional (SSE via `AgentStream`) | 🟡 Medium |
| State management | Stateless per request | ✅ High |
| Observability | OpenTelemetry (stretch goal) | 🟢 Low priority |
| Containerization | Docker Compose: 2 services (Qdrant + App) | ✅ High |

### Open Questions for Implementation

1. **`llama-index-readers-web` GPL-3.0 license** — Is this acceptable for the PoC? Alternative: use `SimpleWebPageReader` (bundled in core, MIT) or write a minimal `requests` + `BeautifulSoup` loader.

2. **Chunk size tuning** — 512 is a good default, but should be validated against actual PDF/web content. May need adjustment per document type.

3. **`similarity_top_k` tuning** — Start with 5, but needs evaluation. Too few = misses relevant context; too many = dilutes with noise and costs more tokens.

4. **Source attribution format** — How should the agent cite sources in responses? Filename? Page number? URL? Needs UX decision.

5. **Ingestion CLI UX** — `python ingest.py --pdf-dir ./data/pdfs --urls ./data/urls.txt`? Or config file? Minor but affects DX.

### Source Documentation

All research was conducted against the following primary sources:

| Source | URL | Accessed |
|--------|-----|----------|
| LlamaIndex Official Docs | https://docs.llamaindex.ai/en/stable/ | 2026-04-22 |
| LlamaIndex PyPI | https://pypi.org/project/llama-index/ | 2026-04-22 |
| LlamaIndex Agent Tutorial | https://docs.llamaindex.ai/en/stable/understanding/agent/ | 2026-04-22 |
| LlamaIndex Multi-Agent Patterns | https://docs.llamaindex.ai/en/stable/understanding/agent/multi_agent/ | 2026-04-22 |
| LlamaIndex Workflows | https://docs.llamaindex.ai/en/stable/understanding/workflows/ | 2026-04-22 |
| LlamaIndex RAG Guide | https://docs.llamaindex.ai/en/stable/understanding/rag/ | 2026-04-22 |
| LlamaIndex Production RAG | https://docs.llamaindex.ai/en/stable/optimizing/production_rag/ | 2026-04-22 |
| LlamaIndex Node Parsers | https://docs.llamaindex.ai/en/stable/module_guides/loading/node_parsers/modules/ | 2026-04-22 |
| LlamaIndex Settings | https://docs.llamaindex.ai/en/stable/module_guides/supporting_modules/settings/ | 2026-04-22 |
| LlamaIndex Evaluation | https://docs.llamaindex.ai/en/stable/module_guides/evaluating/ | 2026-04-22 |
| LlamaIndex Observability | https://docs.llamaindex.ai/en/stable/module_guides/observability/ | 2026-04-22 |
| Qdrant Hybrid Search | https://docs.llamaindex.ai/en/stable/examples/vector_stores/qdrant_hybrid/ | 2026-04-22 |
| OpenAI Embeddings Guide | https://platform.openai.com/docs/guides/embeddings | 2026-04-22 |
| Gradio Mounting Guide | https://www.gradio.app/guides/sharing-your-app | 2026-04-22 |
| llama-index-vector-stores-qdrant | https://pypi.org/project/llama-index-vector-stores-qdrant/ | 2026-04-22 |
| llama-index-readers-web | https://pypi.org/project/llama-index-readers-web/ | 2026-04-22 |

---

**Technical Research Completion Date:** 2026-04-22
**Research Methodology:** Web-verified against official documentation and PyPI
**Source Verification:** All technical claims cited with current sources
**Confidence Level:** High — based on official LlamaIndex documentation (v0.14.21)

---

## Follow-Up Research: Qdrant Configuration & Retrieval Tuning

### Qdrant Collection Setup for Our Stack

For `text-embedding-3-small` (1536 dimensions), the optimal collection configuration:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, SparseVectorParams

client = QdrantClient(host="localhost", port=6333)

# Dense-only collection
client.create_collection(
    collection_name="knowledge_base",
    vectors_config=VectorParams(
        size=1536,          # text-embedding-3-small
        distance=Distance.COSINE,  # standard for OpenAI embeddings
    ),
)

# Hybrid collection (dense + sparse)
client.create_collection(
    collection_name="knowledge_base",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE,
    ),
    sparse_vectors_config={
        "text": SparseVectorParams(),  # BM25 sparse, Dot product by default
    },
)
```

**Distance metric: Cosine** — Qdrant internally normalizes vectors and uses dot product for speed (SIMD-optimized). This is the standard for OpenAI embeddings.

_Source: https://qdrant.tech/documentation/concepts/collections/_

### Qdrant Optimization Strategy for PoC

Qdrant offers three optimization profiles. For our PoC (small dataset, low memory):

| Profile | When to Use | Our Fit |
|---------|-------------|---------|
| High Speed + Low Memory | Large datasets, quantization | ❌ Overkill |
| High Precision + Low Memory | Vectors on disk, HNSW on disk | ❌ Unnecessary for PoC |
| **High Precision + High Speed** | Everything in RAM | ✅ **Best for PoC** |

For a PoC with <10K documents, **default settings are fine** — everything fits in RAM. No need for quantization, on-disk storage, or custom HNSW tuning.

**When to tune later:**
- `hnsw_ef`: Increase for better accuracy at search time (default is usually sufficient for <100K vectors)
- `m`: Increase for better graph connectivity (default 16 is fine for small collections)
- Quantization: Only needed when RAM becomes a constraint (millions of vectors)

_Source: https://qdrant.tech/documentation/guides/optimize/_

### Payload Indexing for Metadata Filtering

Qdrant supports **payload indexes** for efficient filtering. This is powerful for our use case — filtering by document source, type, or date:

```python
# Create payload indexes for metadata fields
client.create_payload_index(
    collection_name="knowledge_base",
    field_name="source_type",    # "pdf" or "web"
    field_schema="keyword",
)
client.create_payload_index(
    collection_name="knowledge_base",
    field_name="file_name",
    field_schema="keyword",
)
```

**Key Qdrant recommendation:** Create payload indexes **immediately after collection creation**, before inserting data. Creating them later blocks updates and misses HNSW optimization opportunities.

This enables filtered queries like:
```python
# Search only within PDFs
query_engine = index.as_query_engine(
    similarity_top_k=5,
    filters=MetadataFilters(
        filters=[ExactMatchFilter(key="source_type", value="pdf")]
    ),
)
```

**Decision impact:** This gives us **Qdrant-level filtering** (more efficient) rather than LlamaIndex node postprocessor filtering (post-retrieval). For our PoC, basic unfiltered search is fine, but metadata indexing is cheap to set up and enables a natural upgrade path.

_Source: https://qdrant.tech/documentation/concepts/indexing/_

### Hybrid Search: Qdrant's Perspective

Qdrant's own article on hybrid search makes several important points that refine our earlier research:

1. **Linear combination of scores doesn't work** — Dense (cosine) and sparse (BM25) scores are not linearly separable. A simple `0.7 * dense + 0.3 * sparse` formula will not reliably distinguish relevant from irrelevant results.

2. **Reciprocal Rank Fusion (RRF) is the recommended default** — Qdrant has built-in RRF support via the Query API. It considers position-based ranking rather than raw scores.

3. **Weighted RRF** (available since Qdrant v1.17) — Allows assigning different weights to dense vs sparse prefetches. Useful if one signal is stronger than the other.

4. **Multi-stage search** is powerful — Prefetch candidates with one method, then rerank with another. E.g., sparse BM25 prefetch → dense rerank, or vice versa.

**How LlamaIndex's `enable_hybrid=True` maps to this:**
- LlamaIndex's Qdrant integration uses `prefetch` with both dense and sparse queries, then fuses via RRF
- The `sparse_top_k` and `similarity_top_k` parameters control candidate count and final results
- LlamaIndex handles all the Qdrant Query API complexity under the hood

**Revised recommendation:** Hybrid search with `fastembed` BM25 is **low cost, high value**. The `fastembed` library runs locally (no API calls), and BM25 sparse vectors are small. Consider including it from MVP rather than deferring.

_Source: https://qdrant.tech/documentation/concepts/hybrid-queries/ , https://qdrant.tech/articles/hybrid-search/_

### Search Parameters: What `similarity_top_k` Really Controls

In the context of hybrid search, the parameters interact as follows:

| Parameter | What it does |
|-----------|-------------|
| `sparse_top_k=12` | Retrieve 12 candidates from each vector space (dense AND sparse) = 24 total candidates |
| `similarity_top_k=5` | After RRF fusion, return the top 5 results |
| `vector_store_query_mode="hybrid"` | Enable hybrid prefetch+fusion |

For dense-only: `similarity_top_k=5` simply retrieves the 5 most similar vectors.

**Tuning guidance:** Start with `similarity_top_k=5, sparse_top_k=12` for hybrid. If answers are missing context, increase `sparse_top_k` (more candidates before fusion). If answers include too much noise, decrease `similarity_top_k`.

---

## Follow-Up Research: Ingestion Pipeline Quality

### PDF Parsing Options

`SimpleDirectoryReader` delegates PDF parsing to the `llama-index-readers-file` package (MIT license, v0.6.0). It includes multiple PDF readers:

| Reader | Library | Quality | Speed | License |
|--------|---------|---------|-------|---------|
| `PDFReader` (default) | pypdf | Basic text extraction | Fast | MIT |
| `PyMuPDFReader` | PyMuPDF/fitz | Better layout handling, preserves structure | Fast | AGPL-3.0 ⚠️ |
| `UnstructuredReader` | unstructured | Best for complex layouts, tables | Slower | Apache 2.0 |
| LlamaParse | Cloud API | State-of-the-art parsing | Depends on network | Paid SaaS |

**Default behavior:** `SimpleDirectoryReader` uses `PDFReader` (pypdf) for `.pdf` files. You can override:

```python
from llama_index.readers.file import PyMuPDFReader, PDFReader

# Use PyMuPDF for better quality (but AGPL license!)
reader = SimpleDirectoryReader(
    input_dir="./data/pdfs",
    file_extractor={".pdf": PyMuPDFReader()},
)

# Or use unstructured for complex documents
from llama_index.readers.file import UnstructuredReader
reader = SimpleDirectoryReader(
    input_dir="./data/pdfs",
    file_extractor={".pdf": UnstructuredReader()},
)
```

**License considerations:**
- `PDFReader` (pypdf) → **MIT** ✅ Safe
- `PyMuPDFReader` → **AGPL-3.0** ⚠️ Copyleft, may require open-sourcing your code if distributed
- `UnstructuredReader` → **Apache 2.0** ✅ Safe, but heavier dependency

**Recommendation for PoC:** Start with the default `PDFReader` (pypdf, MIT). If PDF quality is poor (tables, multi-column layouts), upgrade to `UnstructuredReader` (Apache 2.0) rather than `PyMuPDFReader` (AGPL).

_Source: https://pypi.org/project/llama-index-readers-file/_

### Web Page Loading: Resolving the GPL-3.0 Issue

The `llama-index-readers-web` package is **GPL-3.0** licensed. However, the underlying `trafilatura` library is **Apache 2.0**.

**Options:**

| Approach | License | Quality | Effort |
|----------|---------|---------|--------|
| `llama-index-readers-web` (`TrafilaturaWebReader`) | GPL-3.0 ⚠️ | Best (clean extraction) | Zero |
| Direct `trafilatura` + custom Document wrapper | Apache 2.0 ✅ | Same quality | Minimal |
| `SimpleWebPageReader` (built into core) | MIT ✅ | Basic (raw HTML/text) | Zero |
| Custom `requests` + `BeautifulSoup` | MIT ✅ | Medium (manual extraction) | Some |

**Recommended approach: Direct trafilatura** — Same quality as `TrafilaturaWebReader` but avoids the GPL wrapper:

```python
import trafilatura
from llama_index.core import Document

def load_web_pages(urls: list[str]) -> list[Document]:
    documents = []
    for url in urls:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            text = trafilatura.extract(downloaded, include_links=True)
            if text:
                documents.append(Document(
                    text=text,
                    metadata={"source_url": url, "source_type": "web"},
                ))
    return documents
```

This is ~10 lines of code, Apache 2.0 licensed, and gives the same content extraction quality. No need for the GPL `llama-index-readers-web` package.

_Source: https://pypi.org/project/trafilatura/ (Apache 2.0), https://github.com/run-llama/llama_index (GPL-3.0 for readers-web)_

### Chunking Validation Against Document Types

Different source types may benefit from different chunking approaches:

| Source Type | Characteristics | Chunking Recommendation |
|-------------|----------------|------------------------|
| PDFs (text-heavy) | Long paragraphs, sections | `SentenceSplitter(512, 50)` — default, works well |
| PDFs (tables/structured) | Short cells, column layouts | Smaller chunks (256) or `MarkdownNodeParser` if converted |
| Web pages (articles) | Clean prose after trafilatura | `SentenceSplitter(512, 50)` — works well |
| Web pages (reference/docs) | Short sections, code blocks | `MarkdownNodeParser` → `SentenceSplitter(512, 50)` chained |

**For PoC:** Use a single `SentenceSplitter(512, 50)` for all sources. This is "good enough" and avoids premature optimization. If evaluation reveals poor retrieval on specific document types, add source-specific parsers later.

**Metadata enrichment during ingestion:**
```python
pipeline = IngestionPipeline(
    transformations=[
        SentenceSplitter(chunk_size=512, chunk_overlap=50),
        # Optional: extract titles from chunks
        # TitleExtractor(nodes=5),
        OpenAIEmbedding(model="text-embedding-3-small"),
    ],
    vector_store=vector_store,
)
```

The `TitleExtractor` adds an LLM-generated title to each chunk's metadata — useful for retrieval but costs extra API calls. Skip for MVP.

### Revised Consolidated Decisions (Post Follow-Up)

| Decision | Previous | Revised | Why |
|----------|----------|---------|-----|
| Hybrid search | "Optional, not MVP" | **Include in MVP** | Low cost (fastembed is local), high value per Qdrant's recommendations |
| Web page reader | `TrafilaturaWebReader` (GPL-3.0 ⚠️) | **Direct trafilatura** (Apache 2.0 ✅) | Same quality, ~10 lines of code, no license risk |
| PDF reader | `SimpleDirectoryReader` default | **Keep default** (pypdf, MIT) | Good enough for PoC; upgrade to `UnstructuredReader` if quality issues |
| Payload indexes | Not discussed | **Add from start** | Free to create; enables metadata filtering later |
| Qdrant optimization | Not discussed | **Use defaults** | Everything in RAM for <10K docs; tune only if needed |
| `similarity_top_k` | 5 (guessed) | **5 (dense) or 5+sparse_top_k=12 (hybrid)** | Validated against Qdrant's fusion documentation |

### Additional Sources

| Source | URL | Accessed |
|--------|-----|----------|
| Qdrant Collections Docs | https://qdrant.tech/documentation/concepts/collections/ | 2026-04-22 |
| Qdrant Indexing Docs | https://qdrant.tech/documentation/concepts/indexing/ | 2026-04-22 |
| Qdrant Search Docs | https://qdrant.tech/documentation/concepts/search/ | 2026-04-22 |
| Qdrant Hybrid Queries | https://qdrant.tech/documentation/concepts/hybrid-queries/ | 2026-04-22 |
| Qdrant Optimization Guide | https://qdrant.tech/documentation/guides/optimize/ | 2026-04-22 |
| Qdrant Hybrid Search Article | https://qdrant.tech/articles/hybrid-search/ | 2026-04-22 |
| trafilatura PyPI | https://pypi.org/project/trafilatura/ | 2026-04-22 |
| llama-index-readers-file PyPI | https://pypi.org/project/llama-index-readers-file/ | 2026-04-22 |
| llama-index-readers-web LICENSE | https://github.com/run-llama/llama_index/blob/main/llama-index-integrations/readers/llama-index-readers-web/LICENSE | 2026-04-22 |
