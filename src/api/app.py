"""FastAPI application — routes, Gradio mount, lifespan."""

import logging
import re
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

        # Extract sources from response (agent cites them in text)
        sources = _extract_sources(response_text)

        return QueryResponse(answer=response_text, sources=sources)
    except Exception as e:
        logger.error("Agent error: %s", e)
        raise HTTPException(status_code=500, detail=f"Agent error: {e}") from e


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy")


def _extract_sources(response_text: str) -> list[str]:
    """Extract source references from agent response text.

    Looks for filenames (*.pdf) and URLs in the response.
    """
    sources: list[str] = []

    # Find PDF filenames
    pdf_matches = re.findall(r"[\w\-./]+\.pdf", response_text)
    sources.extend(pdf_matches)

    # Find URLs
    url_matches = re.findall(r"https?://[^\s,)\"']+", response_text)
    sources.extend(url_matches)

    return list(dict.fromkeys(sources))  # deduplicate preserving order


# Gradio chat interface
def _chat_fn(message: str, history: list) -> str:
    """Gradio chat function — bridges sync Gradio to async agent."""
    import asyncio

    if _agent is None:
        return "Agent not initialized. Please wait for startup to complete."

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = pool.submit(asyncio.run, _agent.run(user_msg=message)).result()
        else:
            result = asyncio.run(_agent.run(user_msg=message))
        return str(result)
    except Exception as e:
        return f"Error: {e}"


_demo = gr.ChatInterface(fn=_chat_fn, title="Knowledge Base Agent")
app = gr.mount_gradio_app(app, _demo, path="/chat")
