"""
Memory repository interface - Contract for memory storage operations.
"""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from src.domain.entities.memory import Memory, MemoryType


class IMemoryRepository(ABC):
    """
    Interface for memory repository operations.

    This defines the contract that any memory storage implementation must follow.
    Implementations can use Qdrant, PostgreSQL, or any other storage backend.
    """

    @abstractmethod
    async def create(self, memory: Memory) -> Memory:
        """
        Create a new memory.

        Args:
            memory: Memory entity to create

        Returns:
            Created memory with any generated fields

        Raises:
            VectorStoreError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, memory_id: UUID) -> Memory | None:
        """
        Retrieve a memory by ID.

        Args:
            memory_id: Memory identifier

        Returns:
            Memory if found, None otherwise
        """
        pass

    @abstractmethod
    async def update(self, memory: Memory) -> Memory:
        """
        Update an existing memory.

        Args:
            memory: Memory entity with updated fields

        Returns:
            Updated memory

        Raises:
            EntityNotFoundError: If memory doesn't exist
        """
        pass

    @abstractmethod
    async def delete(self, memory_id: UUID) -> bool:
        """
        Delete a memory.

        Args:
            memory_id: Memory identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def search_similar(
        self,
        query_embedding: list[float],
        user_id: str | None = None,
        limit: int = 5,
        min_score: float = 0.7,
        memory_types: list[MemoryType] | None = None,
    ) -> list[tuple[Memory, float]]:
        """
        Search for similar memories using vector similarity.

        Args:
            query_embedding: Query vector
            user_id: Filter by user ID (optional)
            limit: Maximum number of results
            min_score: Minimum similarity score
            memory_types: Filter by memory types (optional)

        Returns:
            List of (Memory, similarity_score) tuples
        """
        pass

    @abstractmethod
    async def get_by_type(
        self, memory_type: MemoryType, limit: int = 100
    ) -> list[Memory]:
        """
        Get memories by type.

        Args:
            memory_type: Type to filter by
            limit: Maximum number of results

        Returns:
            List of memories
        """
        pass

    @abstractmethod
    async def get_recent(self, limit: int = 10) -> list[Memory]:
        """
        Get most recently created memories.

        Args:
            limit: Maximum number of results

        Returns:
            List of recent memories
        """
        pass

    @abstractmethod
    async def get_frequently_referenced(self, limit: int = 10) -> list[Memory]:
        """
        Get most frequently referenced memories.

        Args:
            limit: Maximum number of results

        Returns:
            List of frequently used memories
        """
        pass

    @abstractmethod
    async def bulk_create(self, memories: list[Memory]) -> list[Memory]:
        """
        Create multiple memories at once.

        Args:
            memories: List of memories to create

        Returns:
            List of created memories
        """
        pass

    @abstractmethod
    async def search_by_text(
        self, query: str, limit: int = 10
    ) -> list[Memory]:
        """
        Search memories by text content.

        Args:
            query: Text query
            limit: Maximum number of results

        Returns:
            List of matching memories
        """
        pass

    @abstractmethod
    async def count(self, memory_type: MemoryType | None = None) -> int:
        """
        Count memories, optionally filtered by type.

        Args:
            memory_type: Type to filter by (optional)

        Returns:
            Number of memories
        """
        pass

    @abstractmethod
    async def delete_stale(self, days_threshold: int = 90) -> int:
        """
        Delete stale memories that haven't been referenced recently.

        Args:
            days_threshold: Number of days to consider stale

        Returns:
            Number of memories deleted
        """
        pass

    @abstractmethod
    async def update_relevance_scores(
        self, decay_factor: float = 0.95
    ) -> int:
        """
        Decay relevance scores for all memories.

        Args:
            decay_factor: Multiplier for relevance decay

        Returns:
            Number of memories updated
        """
        pass
