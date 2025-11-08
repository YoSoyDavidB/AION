"""
Memory entity - Represents a long-term memory item.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class MemoryType(str, Enum):
    """Types of memories that can be stored."""

    PREFERENCE = "preference"  # User preferences (e.g., "prefers concise answers")
    FACT = "fact"  # Factual information (e.g., "user is a software engineer")
    TASK = "task"  # Tasks or to-dos (e.g., "user wants to learn Rust")
    GOAL = "goal"  # Long-term goals (e.g., "build a startup")
    PROFILE = "profile"  # User profile information (e.g., "name is David")


class SensitivityLevel(str, Enum):
    """Sensitivity levels for memory classification."""

    LOW = "low"  # Public information
    MEDIUM = "medium"  # Personal but non-sensitive
    HIGH = "high"  # Sensitive personal information


class Memory(BaseModel):
    """
    Represents a long-term memory item.

    Memories are extracted from conversations and stored for future retrieval.
    They should be concise, factual, and relevant.
    """

    memory_id: UUID = Field(default_factory=uuid4, description="Unique memory identifier")
    user_id: str = Field(..., description="User ID this memory belongs to")
    short_text: str = Field(
        ..., min_length=1, max_length=500, description="The memory content"
    )
    memory_type: MemoryType = Field(..., description="Type of memory")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    last_referenced_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last time memory was retrieved"
    )
    relevance_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Importance score (0-1)"
    )
    num_times_referenced: int = Field(
        default=0, ge=0, description="How many times this memory was used"
    )
    sensitivity: SensitivityLevel = Field(
        default=SensitivityLevel.MEDIUM, description="Sensitivity level"
    )
    embedding: list[float] | None = Field(
        default=None, description="Vector embedding of the memory"
    )
    source: str = Field(..., description="Origin of the memory (conversation ID or file)")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("short_text")
    @classmethod
    def validate_text_length(cls, v: str) -> str:
        """Ensure memory text is concise."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Memory text cannot be empty")
        return stripped

    @field_validator("embedding")
    @classmethod
    def validate_embedding(cls, v: list[float] | None) -> list[float] | None:
        """Validate embedding dimensions if present."""
        if v is not None and len(v) == 0:
            raise ValueError("Embedding cannot be empty if provided")
        return v

    def mark_referenced(self) -> None:
        """Mark this memory as referenced, updating counters and timestamp."""
        self.num_times_referenced += 1
        self.last_referenced_at = datetime.utcnow()

    def decay_relevance(self, decay_factor: float = 0.95) -> None:
        """
        Decay the relevance score over time.

        Args:
            decay_factor: Multiplier for relevance (default 0.95)
        """
        self.relevance_score = max(0.0, self.relevance_score * decay_factor)

    def boost_relevance(self, boost: float = 0.1) -> None:
        """
        Boost the relevance score when memory is used.

        Args:
            boost: Amount to add to relevance (default 0.1)
        """
        self.relevance_score = min(1.0, self.relevance_score + boost)

    def is_stale(self, days_threshold: int = 90) -> bool:
        """
        Check if memory hasn't been referenced recently.

        Args:
            days_threshold: Number of days to consider memory stale

        Returns:
            True if memory is stale
        """
        days_since_reference = (datetime.utcnow() - self.last_referenced_at).days
        return days_since_reference > days_threshold

    def should_consolidate(self, min_references: int = 5) -> bool:
        """
        Determine if memory is important enough to keep.

        Args:
            min_references: Minimum number of references to be considered important

        Returns:
            True if memory should be consolidated/kept
        """
        return (
            self.num_times_referenced >= min_references
            or self.relevance_score > 0.7
            or self.memory_type in [MemoryType.PREFERENCE, MemoryType.PROFILE]
        )

    model_config = {"json_schema_extra": {"example": {
        "memory_id": "550e8400-e29b-41d4-a716-446655440000",
        "short_text": "User prefers concise technical answers",
        "memory_type": "preference",
        "relevance_score": 0.95,
        "sensitivity": "low",
        "source": "conversation_2024_11_07_001",
    }}}
