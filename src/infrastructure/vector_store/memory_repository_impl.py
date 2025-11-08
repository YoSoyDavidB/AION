"""
Qdrant implementation of Memory repository.
"""

from datetime import datetime, timedelta
from uuid import UUID

from qdrant_client.models import FieldCondition, Filter, MatchValue

from src.config.settings import get_settings
from src.domain.entities.memory import Memory, MemoryType
from src.domain.repositories.memory_repository import IMemoryRepository
from src.infrastructure.vector_store.qdrant_client import QdrantClientWrapper
from src.shared.exceptions import EntityNotFoundError, VectorStoreError
from src.shared.logging import LoggerMixin


class QdrantMemoryRepository(IMemoryRepository, LoggerMixin):
    """
    Qdrant implementation of Memory repository.

    Stores memories as vector embeddings with metadata in Qdrant.
    """

    def __init__(self, qdrant_client: QdrantClientWrapper | None = None) -> None:
        """
        Initialize repository.

        Args:
            qdrant_client: Qdrant client instance (optional)
        """
        settings = get_settings()
        self.client = qdrant_client or QdrantClientWrapper()
        self.collection_name = settings.qdrant.qdrant_collection_memories

        self.logger.info(
            "memory_repository_initialized",
            collection=self.collection_name,
        )

    async def initialize(self) -> None:
        """Initialize the collection if it doesn't exist."""
        await self.client.ensure_collection(self.collection_name)

    def _memory_to_payload(self, memory: Memory) -> dict[str, any]:
        """Convert Memory entity to Qdrant payload."""
        return {
            "memory_id": str(memory.memory_id),
            "user_id": memory.user_id,
            "short_text": memory.short_text,
            "memory_type": memory.memory_type.value,
            "timestamp": memory.timestamp.isoformat(),
            "last_referenced_at": memory.last_referenced_at.isoformat(),
            "relevance_score": memory.relevance_score,
            "num_times_referenced": memory.num_times_referenced,
            "sensitivity": memory.sensitivity.value,
            "source": memory.source,
            "metadata": memory.metadata,
        }

    def _payload_to_memory(self, payload: dict[str, any], vector: list[float]) -> Memory:
        """Convert Qdrant payload to Memory entity."""
        return Memory(
            memory_id=UUID(payload["memory_id"]),
            user_id=payload["user_id"],
            short_text=payload["short_text"],
            memory_type=MemoryType(payload["memory_type"]),
            timestamp=datetime.fromisoformat(payload["timestamp"]),
            last_referenced_at=datetime.fromisoformat(payload["last_referenced_at"]),
            relevance_score=payload["relevance_score"],
            num_times_referenced=payload["num_times_referenced"],
            sensitivity=payload["sensitivity"],
            embedding=vector,
            source=payload["source"],
            metadata=payload.get("metadata", {}),
        )

    async def create(self, memory: Memory) -> Memory:
        """Create a new memory."""
        if memory.embedding is None:
            raise VectorStoreError(
                "Memory must have an embedding before storage",
                details={"memory_id": str(memory.memory_id)},
            )

        try:
            payload = self._memory_to_payload(memory)
            await self.client.upsert_point(
                collection_name=self.collection_name,
                point_id=str(memory.memory_id),
                vector=memory.embedding,
                payload=payload,
            )

            self.logger.info(
                "memory_created",
                memory_id=str(memory.memory_id),
                type=memory.memory_type.value,
            )

            return memory

        except Exception as e:
            self.logger.error(
                "memory_creation_failed",
                memory_id=str(memory.memory_id),
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to create memory: {str(e)}",
                details={"memory_id": str(memory.memory_id)},
            ) from e

    async def get_by_id(self, memory_id: UUID) -> Memory | None:
        """Retrieve a memory by ID."""
        try:
            point = await self.client.get_point(
                collection_name=self.collection_name,
                point_id=str(memory_id),
            )

            if point is None:
                return None

            memory = self._payload_to_memory(point["payload"], point["vector"])
            return memory

        except Exception as e:
            self.logger.error(
                "memory_retrieval_failed",
                memory_id=str(memory_id),
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to retrieve memory: {str(e)}",
                details={"memory_id": str(memory_id)},
            ) from e

    async def update(self, memory: Memory) -> Memory:
        """Update an existing memory."""
        # Check if memory exists
        existing = await self.get_by_id(memory.memory_id)
        if existing is None:
            raise EntityNotFoundError("Memory", str(memory.memory_id))

        if memory.embedding is None:
            raise VectorStoreError(
                "Memory must have an embedding for update",
                details={"memory_id": str(memory.memory_id)},
            )

        try:
            payload = self._memory_to_payload(memory)
            await self.client.upsert_point(
                collection_name=self.collection_name,
                point_id=str(memory.memory_id),
                vector=memory.embedding,
                payload=payload,
            )

            self.logger.info(
                "memory_updated",
                memory_id=str(memory.memory_id),
            )

            return memory

        except Exception as e:
            self.logger.error(
                "memory_update_failed",
                memory_id=str(memory.memory_id),
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to update memory: {str(e)}",
                details={"memory_id": str(memory.memory_id)},
            ) from e

    async def delete(self, memory_id: UUID) -> bool:
        """Delete a memory."""
        try:
            deleted = await self.client.delete_point(
                collection_name=self.collection_name,
                point_id=str(memory_id),
            )

            if deleted:
                self.logger.info("memory_deleted", memory_id=str(memory_id))

            return deleted

        except Exception as e:
            self.logger.error(
                "memory_deletion_failed",
                memory_id=str(memory_id),
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to delete memory: {str(e)}",
                details={"memory_id": str(memory_id)},
            ) from e

    async def search_similar(
        self,
        query_embedding: list[float],
        user_id: str | None = None,
        limit: int = 5,
        min_score: float = 0.7,
        memory_types: list[MemoryType] | None = None,
    ) -> list[tuple[Memory, float]]:
        """Search for similar memories."""
        try:
            # Build filter conditions
            filter_conditions = None
            must_conditions = []

            if user_id:
                must_conditions.append(
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id),
                    )
                )

            if memory_types:
                must_conditions.append(
                    FieldCondition(
                        key="memory_type",
                        match=MatchValue(
                            any=[mt.value for mt in memory_types]
                        ),
                    )
                )

            if must_conditions:
                filter_conditions = Filter(must=must_conditions)

            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=min_score,
                filter_conditions=filter_conditions,
            )

            memories_with_scores = []
            for result in results:
                memory = self._payload_to_memory(result.payload, result.vector)
                memories_with_scores.append((memory, result.score))

                # TODO: Implement batch update for marking memories as referenced
                # Currently disabled to prevent search failures
                # memory.mark_referenced()
                # await self.update(memory)

            self.logger.info(
                "memories_searched",
                num_results=len(memories_with_scores),
                min_score=min_score,
            )

            return memories_with_scores

        except Exception as e:
            self.logger.error("memory_search_failed", error=str(e))
            raise VectorStoreError(
                f"Failed to search memories: {str(e)}"
            ) from e

    async def get_by_type(
        self, memory_type: MemoryType, limit: int = 100
    ) -> list[Memory]:
        """Get memories by type."""
        try:
            filter_conditions = Filter(
                must=[
                    FieldCondition(
                        key="memory_type",
                        match=MatchValue(value=memory_type.value),
                    )
                ]
            )

            # Use scroll to get all matching points
            results, _ = await self.client.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_conditions,
                limit=limit,
                with_vectors=True,
            )

            memories = [
                self._payload_to_memory(point.payload, point.vector)
                for point in results
            ]

            return memories

        except Exception as e:
            self.logger.error(
                "get_by_type_failed",
                memory_type=memory_type.value,
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to get memories by type: {str(e)}"
            ) from e

    async def get_recent(self, limit: int = 10) -> list[Memory]:
        """Get most recently created memories."""
        try:
            # Scroll through all memories and sort by timestamp
            results, _ = await self.client.client.scroll(
                collection_name=self.collection_name,
                limit=limit * 10,  # Get more to sort
                with_vectors=True,
            )

            memories = [
                self._payload_to_memory(point.payload, point.vector)
                for point in results
            ]

            # Sort by timestamp and limit
            memories.sort(key=lambda m: m.timestamp, reverse=True)
            return memories[:limit]

        except Exception as e:
            self.logger.error("get_recent_failed", error=str(e))
            raise VectorStoreError(
                f"Failed to get recent memories: {str(e)}"
            ) from e

    async def get_frequently_referenced(self, limit: int = 10) -> list[Memory]:
        """Get most frequently referenced memories."""
        try:
            results, _ = await self.client.client.scroll(
                collection_name=self.collection_name,
                limit=limit * 10,
                with_vectors=True,
            )

            memories = [
                self._payload_to_memory(point.payload, point.vector)
                for point in results
            ]

            # Sort by reference count
            memories.sort(key=lambda m: m.num_times_referenced, reverse=True)
            return memories[:limit]

        except Exception as e:
            self.logger.error("get_frequently_referenced_failed", error=str(e))
            raise VectorStoreError(
                f"Failed to get frequently referenced memories: {str(e)}"
            ) from e

    async def bulk_create(self, memories: list[Memory]) -> list[Memory]:
        """Create multiple memories at once."""
        try:
            points = []
            for memory in memories:
                if memory.embedding is None:
                    raise VectorStoreError(
                        "All memories must have embeddings",
                        details={"memory_id": str(memory.memory_id)},
                    )

                payload = self._memory_to_payload(memory)
                points.append((str(memory.memory_id), memory.embedding, payload))

            await self.client.upsert_points(self.collection_name, points)

            self.logger.info("bulk_memories_created", count=len(memories))

            return memories

        except Exception as e:
            self.logger.error("bulk_create_failed", error=str(e))
            raise VectorStoreError(
                f"Failed to bulk create memories: {str(e)}"
            ) from e

    async def search_by_text(self, query: str, limit: int = 10) -> list[Memory]:
        """Search memories by text content."""
        # Note: This requires embeddings for the query text
        # In practice, this would call the embedding service
        # For now, return empty list
        self.logger.warning("text_search_not_implemented")
        return []

    async def count(self, memory_type: MemoryType | None = None) -> int:
        """Count memories, optionally filtered by type."""
        try:
            filter_conditions = None
            if memory_type:
                filter_conditions = Filter(
                    must=[
                        FieldCondition(
                            key="memory_type",
                            match=MatchValue(value=memory_type.value),
                        )
                    ]
                )

            count = await self.client.count_points(
                self.collection_name, filter_conditions
            )

            return count

        except Exception as e:
            self.logger.error("count_failed", error=str(e))
            raise VectorStoreError(f"Failed to count memories: {str(e)}") from e

    async def delete_stale(self, days_threshold: int = 90) -> int:
        """Delete stale memories."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

            # Get all memories and filter in application
            results, _ = await self.client.client.scroll(
                collection_name=self.collection_name,
                limit=10000,
                with_vectors=True,
            )

            stale_ids = []
            for point in results:
                last_ref = datetime.fromisoformat(point.payload["last_referenced_at"])
                if last_ref < cutoff_date:
                    stale_ids.append(point.id)

            if stale_ids:
                for memory_id in stale_ids:
                    await self.client.delete_point(self.collection_name, memory_id)

            self.logger.info("stale_memories_deleted", count=len(stale_ids))

            return len(stale_ids)

        except Exception as e:
            self.logger.error("delete_stale_failed", error=str(e))
            raise VectorStoreError(
                f"Failed to delete stale memories: {str(e)}"
            ) from e

    async def update_relevance_scores(self, decay_factor: float = 0.95) -> int:
        """Decay relevance scores for all memories."""
        try:
            results, _ = await self.client.client.scroll(
                collection_name=self.collection_name,
                limit=10000,
                with_vectors=True,
            )

            updated_count = 0
            for point in results:
                memory = self._payload_to_memory(point.payload, point.vector)
                memory.decay_relevance(decay_factor)
                await self.update(memory)
                updated_count += 1

            self.logger.info(
                "relevance_scores_updated",
                count=updated_count,
                decay_factor=decay_factor,
            )

            return updated_count

        except Exception as e:
            self.logger.error("update_relevance_failed", error=str(e))
            raise VectorStoreError(
                f"Failed to update relevance scores: {str(e)}"
            ) from e
