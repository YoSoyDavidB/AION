"""
DTOs for document operations.
"""

from uuid import UUID

from pydantic import BaseModel, Field


class DocumentUploadRequest(BaseModel):
    """Request to upload and process a document."""

    user_id: str = Field(..., description="User ID this document belongs to")
    title: str = Field(..., min_length=1, max_length=200, description="Document title")
    tags: list[str] = Field(default_factory=list, description="Document tags for organization")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class DocumentChunkResponse(BaseModel):
    """Response containing document chunk information."""

    doc_id: UUID = Field(..., description="Document identifier")
    chunk_id: str = Field(..., description="Chunk identifier")
    path: str = Field(..., description="Document path/title")
    content: str = Field(..., description="Chunk content")
    tags: list[str] = Field(..., description="Document tags")
    chunk_index: int = Field(..., description="Chunk index in document")
    total_chunks: int = Field(..., description="Total chunks in document")


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""

    doc_id: UUID = Field(..., description="Document identifier")
    title: str = Field(..., description="Document title")
    num_chunks: int = Field(..., description="Number of chunks created")
    total_characters: int = Field(..., description="Total characters processed")
    tags: list[str] = Field(..., description="Document tags")


class DocumentSearchRequest(BaseModel):
    """Request to search for documents."""

    user_id: str = Field(..., description="User ID to filter documents")
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum results")
    min_score: float = Field(
        default=0.3, ge=0.0, le=1.0, description="Minimum similarity score"
    )
    tags: list[str] | None = Field(default=None, description="Filter by tags")
