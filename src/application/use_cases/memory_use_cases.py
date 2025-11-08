"""
Use cases for memory management.
"""

from uuid import UUID

from src.application.dtos.memory_dto import (
    MemoryCreateRequest,
    MemoryResponse,
    MemorySearchRequest,
)
from src.domain.entities.memory import Memory
from src.domain.repositories.memory_repository import IMemoryRepository
from src.infrastructure.embeddings.embedding_service import EmbeddingService
from src.shared.exceptions import UseCaseExecutionError
from src.shared.logging import LoggerMixin


class CreateMemoryUseCase(LoggerMixin):
    """Use case for creating a new memory."""

    def __init__(
        self,
        memory_repo: IMemoryRepository,
        embedding_service: EmbeddingService,
    ) -> None:
        self.memory_repo = memory_repo
        self.embedding_service = embedding_service

    async def execute(self, request: MemoryCreateRequest) -> MemoryResponse:
        """
        Create a new memory with embedding.

        Args:
            request: Memory creation request

        Returns:
            Created memory response

        Raises:
            UseCaseExecutionError: If creation fails
        """
        try:
            self.logger.info(
                "creating_memory",
                text=request.short_text[:50],
                type=request.memory_type.value,
            )

            # Generate embedding for the memory text
            embedding = await self.embedding_service.embed_text(request.short_text)

            # Create memory entity
            memory = Memory(
                user_id=request.user_id,
                short_text=request.short_text,
                memory_type=request.memory_type,
                sensitivity=request.sensitivity,
                source=request.source,
                relevance_score=request.relevance_score,
                embedding=embedding,
                metadata=request.metadata,
            )

            # Store in repository
            created_memory = await self.memory_repo.create(memory)

            self.logger.info(
                "memory_created",
                memory_id=str(created_memory.memory_id),
            )

            # Convert to response
            return self._to_response(created_memory)

        except Exception as e:
            self.logger.error("create_memory_failed", error=str(e))
            raise UseCaseExecutionError(
                f"Failed to create memory: {str(e)}"
            ) from e

    def _to_response(self, memory: Memory) -> MemoryResponse:
        """Convert Memory entity to MemoryResponse DTO."""
        return MemoryResponse(
            memory_id=memory.memory_id,
            short_text=memory.short_text,
            memory_type=memory.memory_type,
            sensitivity=memory.sensitivity,
            relevance_score=memory.relevance_score,
            num_times_referenced=memory.num_times_referenced,
            source=memory.source,
            created_at=memory.timestamp.isoformat(),
            last_referenced_at=memory.last_referenced_at.isoformat(),
        )


class SearchMemoriesUseCase(LoggerMixin):
    """Use case for searching memories by semantic similarity."""

    def __init__(
        self,
        memory_repo: IMemoryRepository,
        embedding_service: EmbeddingService,
    ) -> None:
        self.memory_repo = memory_repo
        self.embedding_service = embedding_service

    async def execute(
        self, request: MemorySearchRequest
    ) -> list[tuple[MemoryResponse, float]]:
        """
        Search for similar memories.

        Args:
            request: Memory search request

        Returns:
            List of (MemoryResponse, similarity_score) tuples

        Raises:
            UseCaseExecutionError: If search fails
        """
        try:
            self.logger.info(
                "searching_memories",
                query=request.query[:50],
                limit=request.limit,
            )

            # Generate embedding for the query
            query_embedding = await self.embedding_service.embed_query(request.query)

            # Search in repository
            results = await self.memory_repo.search_similar(
                query_embedding=query_embedding,
                user_id=request.user_id,
                limit=request.limit,
                min_score=request.min_score,
                memory_types=request.memory_types,
            )

            self.logger.info("memories_found", count=len(results))

            # Convert to responses
            return [
                (self._to_response(memory), score) for memory, score in results
            ]

        except Exception as e:
            self.logger.error("search_memories_failed", error=str(e))
            raise UseCaseExecutionError(
                f"Failed to search memories: {str(e)}"
            ) from e

    def _to_response(self, memory: Memory) -> MemoryResponse:
        """Convert Memory entity to MemoryResponse DTO."""
        return MemoryResponse(
            memory_id=memory.memory_id,
            short_text=memory.short_text,
            memory_type=memory.memory_type,
            sensitivity=memory.sensitivity,
            relevance_score=memory.relevance_score,
            num_times_referenced=memory.num_times_referenced,
            source=memory.source,
            created_at=memory.timestamp.isoformat(),
            last_referenced_at=memory.last_referenced_at.isoformat(),
        )


class GetMemoryByIdUseCase(LoggerMixin):
    """Use case for retrieving a memory by ID."""

    def __init__(self, memory_repo: IMemoryRepository) -> None:
        self.memory_repo = memory_repo

    async def execute(self, memory_id: UUID) -> MemoryResponse | None:
        """
        Get memory by ID.

        Args:
            memory_id: Memory identifier

        Returns:
            Memory response or None if not found

        Raises:
            UseCaseExecutionError: If retrieval fails
        """
        try:
            memory = await self.memory_repo.get_by_id(memory_id)

            if memory is None:
                return None

            return MemoryResponse(
                memory_id=memory.memory_id,
                short_text=memory.short_text,
                memory_type=memory.memory_type,
                sensitivity=memory.sensitivity,
                relevance_score=memory.relevance_score,
                num_times_referenced=memory.num_times_referenced,
                source=memory.source,
                created_at=memory.timestamp.isoformat(),
                last_referenced_at=memory.last_referenced_at.isoformat(),
            )

        except Exception as e:
            self.logger.error(
                "get_memory_failed",
                memory_id=str(memory_id),
                error=str(e),
            )
            raise UseCaseExecutionError(
                f"Failed to get memory: {str(e)}"
            ) from e


class DeleteMemoryUseCase(LoggerMixin):
    """Use case for deleting a memory."""

    def __init__(self, memory_repo: IMemoryRepository) -> None:
        self.memory_repo = memory_repo

    async def execute(self, memory_id: UUID) -> bool:
        """
        Delete a memory.

        Args:
            memory_id: Memory identifier

        Returns:
            True if deleted, False if not found

        Raises:
            UseCaseExecutionError: If deletion fails
        """
        try:
            self.logger.info("deleting_memory", memory_id=str(memory_id))

            deleted = await self.memory_repo.delete(memory_id)

            if deleted:
                self.logger.info("memory_deleted", memory_id=str(memory_id))
            else:
                self.logger.warning("memory_not_found", memory_id=str(memory_id))

            return deleted

        except Exception as e:
            self.logger.error(
                "delete_memory_failed",
                memory_id=str(memory_id),
                error=str(e),
            )
            raise UseCaseExecutionError(
                f"Failed to delete memory: {str(e)}"
            ) from e


class ConsolidateMemoriesUseCase(LoggerMixin):
    """Use case for consolidating and cleaning up memories."""

    def __init__(self, memory_repo: IMemoryRepository) -> None:
        self.memory_repo = memory_repo

    async def execute(
        self, decay_factor: float = 0.95, stale_days: int = 90
    ) -> dict[str, int]:
        """
        Consolidate memories by decaying relevance and removing stale ones.

        Args:
            decay_factor: Relevance decay factor
            stale_days: Days threshold for stale memories

        Returns:
            Dictionary with consolidation statistics

        Raises:
            UseCaseExecutionError: If consolidation fails
        """
        try:
            self.logger.info(
                "consolidating_memories",
                decay_factor=decay_factor,
                stale_days=stale_days,
            )

            # Decay relevance scores
            updated_count = await self.memory_repo.update_relevance_scores(
                decay_factor
            )

            # Delete stale memories
            deleted_count = await self.memory_repo.delete_stale(stale_days)

            stats = {
                "updated": updated_count,
                "deleted": deleted_count,
            }

            self.logger.info("memories_consolidated", stats=stats)

            return stats

        except Exception as e:
            self.logger.error("consolidate_memories_failed", error=str(e))
            raise UseCaseExecutionError(
                f"Failed to consolidate memories: {str(e)}"
            ) from e
