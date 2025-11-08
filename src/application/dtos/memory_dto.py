"""
DTOs for memory operations.
"""

from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities.memory import MemoryType, SensitivityLevel


class MemoryCreateRequest(BaseModel):
    """Request to create a new memory."""

    user_id: str = Field(..., description="User ID this memory belongs to")
    short_text: str = Field(..., min_length=1, max_length=500, description="Memory content")
    memory_type: MemoryType = Field(..., description="Type of memory")
    sensitivity: SensitivityLevel = Field(
        default=SensitivityLevel.MEDIUM, description="Sensitivity level"
    )
    source: str = Field(..., description="Origin of the memory")
    relevance_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Initial relevance score"
    )
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class MemoryResponse(BaseModel):
    """Response containing memory information."""

    memory_id: UUID = Field(..., description="Memory identifier")
    short_text: str = Field(..., description="Memory content")
    memory_type: MemoryType = Field(..., description="Type of memory")
    sensitivity: SensitivityLevel = Field(..., description="Sensitivity level")
    relevance_score: float = Field(..., description="Relevance score")
    num_times_referenced: int = Field(..., description="Reference count")
    source: str = Field(..., description="Origin of the memory")
    created_at: str = Field(..., description="Creation timestamp")
    last_referenced_at: str = Field(..., description="Last reference timestamp")


class MemorySearchRequest(BaseModel):
    """Request to search for memories."""

    user_id: str = Field(..., description="User ID to filter memories")
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum results")
    min_score: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum similarity score"
    )
    memory_types: list[MemoryType] | None = Field(
        default=None, description="Filter by memory types"
    )
