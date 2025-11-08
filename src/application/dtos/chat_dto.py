"""
DTOs for chat operations.
"""

from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request for chat conversation."""

    user_id: str = Field(..., description="User identifier")
    message: str = Field(..., min_length=1, description="User message")
    conversation_id: UUID | None = Field(
        default=None, description="Existing conversation ID (optional)"
    )
    use_memory: bool = Field(default=True, description="Use long-term memory")
    use_knowledge_base: bool = Field(default=True, description="Search knowledge base")
    use_tools: bool = Field(
        default=True, description="Enable function calling / tool use"
    )
    tool_choice: str | None = Field(
        default=None,
        description="Tool choice: 'auto' (default), 'none', or specific tool name (e.g., 'calculator')",
    )
    max_context_memories: int = Field(
        default=5, ge=1, le=20, description="Max memories to retrieve"
    )
    max_context_documents: int = Field(
        default=10, ge=1, le=50, description="Max documents to retrieve"
    )


class ChatResponse(BaseModel):
    """Response from chat conversation."""

    conversation_id: UUID = Field(..., description="Conversation ID")
    message: str = Field(..., description="Assistant response")
    memories_used: list[str] = Field(
        default_factory=list, description="Memory IDs used in response"
    )
    documents_used: list[str] = Field(
        default_factory=list, description="Document IDs used in response"
    )
    new_memories_created: list[str] = Field(
        default_factory=list, description="New memory IDs created"
    )
    tools_used: list[dict] = Field(
        default_factory=list,
        description="Tools/functions called during response generation",
    )
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
