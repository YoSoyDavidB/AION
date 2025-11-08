"""
Document entity - Represents a knowledge base document chunk.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class SourceType(str):
    """Document source types."""

    OBSIDIAN = "obsidian"
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    WEB = "web"


class Document(BaseModel):
    """
    Represents a document chunk from the knowledge base.

    Documents are chunked from larger files (Obsidian notes, PDFs, etc.)
    and stored with embeddings for semantic search.
    """

    doc_id: UUID = Field(default_factory=uuid4, description="Document identifier")
    user_id: str = Field(..., description="User ID this document belongs to")
    chunk_id: str = Field(..., description="Unique chunk identifier (hash)")
    path: str = Field(..., description="File path in the knowledge base")
    title: str = Field(default="", min_length=0, description="Document title")
    content: str = Field(..., min_length=1, description="Chunk content")
    heading: str | None = Field(default=None, description="Markdown section heading")
    tags: list[str] = Field(default_factory=list, description="Associated tags")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="File creation date"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update date"
    )
    language: str = Field(default="en", description="Content language")
    embedding: list[float] | None = Field(
        default=None, description="Vector embedding of the chunk"
    )
    source_type: str = Field(default=SourceType.OBSIDIAN, description="Document source type")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    char_count: int = Field(default=0, ge=0, description="Character count")
    token_count: int = Field(default=0, ge=0, description="Approximate token count")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Ensure content is not empty."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Document content cannot be empty")
        return stripped

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: list[str]) -> list[str]:
        """Normalize tags to lowercase and remove duplicates."""
        return sorted(list(set(tag.lower().strip() for tag in v if tag.strip())))

    @field_validator("embedding")
    @classmethod
    def validate_embedding(cls, v: list[float] | None) -> list[float] | None:
        """Validate embedding dimensions if present."""
        if v is not None and len(v) == 0:
            raise ValueError("Embedding cannot be empty if provided")
        return v

    def calculate_metrics(self) -> None:
        """Calculate character and approximate token counts."""
        self.char_count = len(self.content)
        # Rough approximation: 1 token ≈ 4 characters
        self.token_count = self.char_count // 4

    def has_tag(self, tag: str) -> bool:
        """
        Check if document has a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            True if tag exists
        """
        return tag.lower() in self.tags

    def add_tag(self, tag: str) -> None:
        """
        Add a tag to the document.

        Args:
            tag: Tag to add
        """
        normalized_tag = tag.lower().strip()
        if normalized_tag and normalized_tag not in self.tags:
            self.tags.append(normalized_tag)
            self.tags.sort()

    def remove_tag(self, tag: str) -> None:
        """
        Remove a tag from the document.

        Args:
            tag: Tag to remove
        """
        normalized_tag = tag.lower().strip()
        if normalized_tag in self.tags:
            self.tags.remove(normalized_tag)

    def is_recent(self, days_threshold: int = 30) -> bool:
        """
        Check if document was updated recently.

        Args:
            days_threshold: Number of days to consider recent

        Returns:
            True if document is recent
        """
        days_since_update = (datetime.utcnow() - self.updated_at).days
        return days_since_update <= days_threshold

    model_config = {"json_schema_extra": {"example": {
        "doc_id": "550e8400-e29b-41d4-a716-446655440000",
        "chunk_id": "hash_abc123",
        "path": "notes/programming/python.md",
        "title": "Python Best Practices",
        "content": "Always use type hints in Python 3.11+...",
        "heading": "Type Hints",
        "tags": ["python", "programming", "best-practices"],
        "language": "en",
        "source_type": "obsidian",
    }}}
