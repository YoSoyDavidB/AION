"""
DTOs for RAG (Retrieval-Augmented Generation) operations.
"""

from pydantic import BaseModel, Field

from src.application.dtos.memory_dto import MemoryResponse


class RAGContext(BaseModel):
    """Context assembled for RAG."""

    memories: list[MemoryResponse] = Field(
        default_factory=list, description="Retrieved memories"
    )
    documents: list[dict] = Field(default_factory=list, description="Retrieved documents")
    context_text: str = Field(..., description="Assembled context text")
    total_tokens: int = Field(..., description="Approximate token count")


class RAGRequest(BaseModel):
    """Request for RAG-based question answering."""

    query: str = Field(..., min_length=1, description="User query")
    user_id: str = Field(..., description="User identifier")
    include_memories: bool = Field(default=True, description="Include memory context")
    include_documents: bool = Field(default=True, description="Include document context")
    use_tools: bool = Field(default=True, description="Enable function calling / tool use")
    tool_choice: str | None = Field(
        default=None,
        description="Tool choice: 'auto' (default), 'none', or specific tool name",
    )
    max_memories: int = Field(default=5, ge=0, le=20, description="Max memories")
    max_documents: int = Field(default=10, ge=0, le=50, description="Max documents")
    system_prompt: str | None = Field(default=None, description="Custom system prompt")


class RAGResponse(BaseModel):
    """Response from RAG-based question answering."""

    answer: str = Field(..., description="Generated answer")
    context: RAGContext = Field(..., description="Context used for generation")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence score"
    )
    sources: list[str] = Field(default_factory=list, description="Source citations")
    tools_used: list[dict] = Field(
        default_factory=list,
        description="Tools/functions called during answer generation",
    )
