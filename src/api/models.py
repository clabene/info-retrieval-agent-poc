"""Pydantic request/response models for the API."""

from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Request body for POST /query."""

    question: str


class QueryResponse(BaseModel):
    """Response body for POST /query."""

    answer: str
    sources: list[str]


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str
