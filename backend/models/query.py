from typing import Any, Literal

from pydantic import BaseModel, Field


Confidence = Literal["high", "medium", "low", "insufficient"]


class QueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=5000)
    stream: bool = False


class ClaimCitation(BaseModel):
    claim: str
    chunk_id: str
    quote: str


class QueryResponse(BaseModel):
    direct_answer: str = ""
    explanation: list[ClaimCitation] = Field(default_factory=list)
    confidence: Confidence = "insufficient"
    conflicting_sources: list[dict[str, Any]] | None = None
    validation_warnings: list[str] | None = None
    message: str | None = None


class UploadResponse(BaseModel):
    filename: str
    chunks_indexed: int
    message: str


class QueryAnalysis(BaseModel):
    region: str
    system: str
    concept_type: str
    complexity: str
    sub_questions: list[str]
    is_anatomy: bool
    sources_needed: list[str]
