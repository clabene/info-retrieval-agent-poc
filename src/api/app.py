"""FastAPI application — routes, Gradio mount, lifespan."""

import logging
from contextlib import asynccontextmanager

import gradio as gr
from fastapi import FastAPI, HTTPException

from src.api.models import HealthResponse, QueryRequest, QueryResponse
from src.core.agent import build_agent

logger = logging.getLogger(__name__)

# Module-level agent reference, initialized during lifespan
_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize agent on startup."""
    global _agent
    logger.info("Initializing agent...")
    _agent = build_agent()
    logger.info("Agent ready.")
    yield
    _agent = None


app = FastAPI(title="Info Retrieval Agent", lifespan=lifespan)


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """Submit a natural-language question and receive a synthesized answer."""
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        response = await _agent.run(user_msg=request.question)
        response_text = str(response)

        # Extract sources from agent tool call results (source nodes metadata)
        sources = _extract_sources_from_tool_calls(response)

        return QueryResponse(answer=response_text, sources=sources)
    except Exception as e:
        logger.error("Agent error: %s", e)
        raise HTTPException(status_code=500, detail=f"Agent error: {e}") from e


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy")


def _extract_sources_from_tool_calls(response) -> list[str]:
    """Extract source references from agent tool call results.

    Reads source_nodes metadata from QueryEngineTool responses
    to get file names, page numbers, and URLs.
    """
    sources: list[str] = []

    if not hasattr(response, "tool_calls"):
        return sources

    for tool_call in response.tool_calls:
        raw_output = getattr(tool_call, "tool_output", None)
        if raw_output is None:
            continue

        raw_response = getattr(raw_output, "raw_output", None)
        if raw_response is None:
            continue

        source_nodes = getattr(raw_response, "source_nodes", [])
        for node in source_nodes:
            metadata = getattr(node, "metadata", {}) if hasattr(node, "metadata") else {}
            if not metadata:
                node_obj = getattr(node, "node", None)
                metadata = getattr(node_obj, "metadata", {}) if node_obj else {}

            file_name = metadata.get("file_name", "")
            page_label = metadata.get("page_label", "")
            source_url = metadata.get("source_url", "")

            if source_url:
                sources.append(source_url)
            elif file_name and page_label:
                sources.append(f"{file_name} (p. {page_label})")
            elif file_name:
                sources.append(file_name)

    return list(dict.fromkeys(sources))  # deduplicate preserving order


# Gradio chat interface
async def _chat_fn(message: str, history: list) -> str:
    """Gradio chat function — async, invokes agent directly."""
    if not message or not message.strip():
        return ""

    if _agent is None:
        return "Agent not initialized. Please wait for startup to complete."

    try:
        response = await _agent.run(user_msg=message)
        return str(response)
    except Exception as e:
        return f"Error: {e}"


# JS to hide PWA and Screen Studio sections from Gradio settings
# Note: Gradio's settings panel is part of its internal frontend shell.
# When mounted via mount_gradio_app, neither head/js/css on Blocks can target it.
# These sections are cosmetic — left visible as a known Gradio limitation.


with gr.Blocks() as _demo:
    gr.ChatInterface(
        fn=_chat_fn,
        title="Knowledge Base Agent",
        chatbot=gr.Chatbot(buttons=["copy", "copy_all"]),
    )

app = gr.mount_gradio_app(app, _demo, path="/chat")
