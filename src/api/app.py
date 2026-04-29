"""FastAPI application — routes, Gradio mount, lifespan."""

import logging
from contextlib import asynccontextmanager

import gradio as gr
from fastapi import FastAPI, HTTPException

from src.api.models import HealthResponse, QueryRequest, QueryResponse
from src.core.agent import build_agent, get_last_sources, init_sources

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
        init_sources()
        response = await _agent.run(user_msg=request.question)
        response_text = str(response)

        # Deduplicate sources captured by the tool wrapper, preserving order
        sources = list(dict.fromkeys(get_last_sources()))

        return QueryResponse(answer=response_text, sources=sources)
    except Exception as e:
        logger.error("Agent error: %s", e)
        raise HTTPException(status_code=500, detail=f"Agent error: {e}") from e


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(status="healthy")


# Gradio chat interface
async def _chat_fn(message: str, history: list) -> str:
    """Gradio chat function — async, invokes agent directly."""
    if not message or not message.strip():
        return ""

    if _agent is None:
        return "Agent not initialized. Please wait for startup to complete."

    try:
        init_sources()
        response = await _agent.run(user_msg=message)
        answer = str(response)

        # Append deduplicated sources as markdown links
        sources = list(dict.fromkeys(get_last_sources()))
        if sources:
            answer += "\n\n---\n**Sources:**\n"
            for src in sources:
                if src.startswith("http"):
                    answer += f"- [{src}]({src})\n"
                else:
                    answer += f"- {src}\n"

        return answer
    except Exception as e:
        return f"Error: {e}"


with gr.Blocks(fill_height=True) as _demo:
    gr.ChatInterface(
        fn=_chat_fn,
        title="Knowledge Base Agent",
        chatbot=gr.Chatbot(buttons=["copy", "copy_all"], height="75vh"),
        fill_height=True,
    )

app = gr.mount_gradio_app(app, _demo, path="/chat")
