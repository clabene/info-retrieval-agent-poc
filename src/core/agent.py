"""Agent construction — FunctionAgent with QueryEngineTool for agentic retrieval."""

import logging
from contextvars import ContextVar

from llama_index.core import Settings as LlamaSettings
from llama_index.core import VectorStoreIndex
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import QueryEngineTool, ToolOutput

from src.config.providers import get_embed_model, get_llm, get_vector_store

logger = logging.getLogger(__name__)

# Per-request collector for source nodes produced by tool calls.
# Populated by the wrapped tool, read + cleared by the /query endpoint.
# Uses ContextVar so concurrent async requests don't leak sources.
_last_sources_var: ContextVar[list[str]] = ContextVar("last_sources", default=[])


def get_last_sources() -> list[str]:
    """Return the per-request sources list (creates one if needed)."""
    return _last_sources_var.get()


def init_sources() -> None:
    """Reset the per-request sources list. Call before each agent.run()."""
    _last_sources_var.set([])

SYSTEM_PROMPT = """\
You are an information retrieval agent. Your job is to answer questions \
using ONLY the knowledge_base tool provided to you.

Rules:
1. ALWAYS use the knowledge_base tool to search for relevant information before answering.
2. If the tool returns relevant information, synthesize a clear answer and cite which documents your answer is based on.
3. If the tool returns no relevant information, say clearly: \
"I could not find information about this in the knowledge base."
4. Do NOT make up information or answer from your general knowledge.
5. If the initial search doesn't fully answer the question, reformulate your query and search again.
6. Keep answers concise but comprehensive.
"""


def build_query_engine_tool() -> QueryEngineTool:
    """Build a QueryEngineTool over the Qdrant vector store with hybrid search.

    Returns:
        QueryEngineTool configured with similarity_top_k=5, sparse_top_k=12, hybrid mode.
    """
    vector_store = get_vector_store()

    # Set LlamaIndex global settings to prevent it from defaulting to OpenAI
    embed_model = get_embed_model()
    llm = get_llm()
    LlamaSettings.embed_model = embed_model
    LlamaSettings.llm = llm

    index = VectorStoreIndex.from_vector_store(vector_store)
    query_engine = index.as_query_engine(
        similarity_top_k=5,
        sparse_top_k=12,
        vector_store_query_mode="hybrid",
    )
    tool = QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="knowledge_base",
        description=(
            "Search the knowledge base for information from ingested documents. "
            "Use this tool to find answers to questions about the indexed content. "
            "Input should be a natural language question or search query."
        ),
    )

    # Monkey-patch call() to capture source_nodes as a side-effect.
    # We keep QueryEngineTool (not FunctionTool) so FunctionAgent invokes it.
    _original_call = tool.call

    def _call_with_source_capture(*args, **kwargs) -> ToolOutput:
        output = _original_call(*args, **kwargs)
        _collect_sources(output)
        return output

    tool.call = _call_with_source_capture  # type: ignore[method-assign]

    # Same for async path
    _original_acall = tool.acall

    async def _acall_with_source_capture(*args, **kwargs) -> ToolOutput:
        output = await _original_acall(*args, **kwargs)
        _collect_sources(output)
        return output

    tool.acall = _acall_with_source_capture  # type: ignore[method-assign]

    return tool


def _collect_sources(tool_output: ToolOutput) -> None:
    """Extract source metadata from a ToolOutput and append to per-request sources."""
    raw_response = getattr(tool_output, "raw_output", None)
    source_nodes = getattr(raw_response, "source_nodes", []) if raw_response else []
    sources = get_last_sources()
    for sn in source_nodes:
        node = getattr(sn, "node", sn)
        meta = getattr(node, "metadata", {})
        source_url = meta.get("source_url", "")
        file_name = meta.get("file_name", "")
        page_label = meta.get("page_label", "")
        if source_url:
            sources.append(source_url)
        elif file_name and page_label:
            sources.append(f"{file_name} (p. {page_label})")
        elif file_name:
            sources.append(file_name)


def build_agent() -> FunctionAgent:
    """Build the FunctionAgent with the knowledge base query tool.

    Returns:
        FunctionAgent configured with GPT-4o-mini and the QueryEngineTool.
    """
    llm = get_llm()
    tool = build_query_engine_tool()

    agent = FunctionAgent(
        tools=[tool],
        llm=llm,
        system_prompt=SYSTEM_PROMPT,
        initial_tool_choice="required",
    )

    logger.info("Agent built with tool: %s", tool.metadata.name)
    return agent
