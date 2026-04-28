"""Agent construction — FunctionAgent with QueryEngineTool for agentic retrieval."""

import logging

from llama_index.core import VectorStoreIndex
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.tools import QueryEngineTool

from src.config.providers import get_llm, get_vector_store

logger = logging.getLogger(__name__)

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
    index = VectorStoreIndex.from_vector_store(vector_store)
    query_engine = index.as_query_engine(
        similarity_top_k=5,
        sparse_top_k=12,
        vector_store_query_mode="hybrid",
    )
    return QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="knowledge_base",
        description=(
            "Search the knowledge base for information from ingested documents. "
            "Use this tool to find answers to questions about the indexed content. "
            "Input should be a natural language question or search query."
        ),
    )


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
    )

    logger.info("Agent built with tool: %s", tool.metadata.name)
    return agent
