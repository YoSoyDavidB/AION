"""
Qdrant client wrapper for vector store operations.
"""

from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from src.config.settings import get_settings
from src.shared.exceptions import VectorStoreError
from src.shared.logging import LoggerMixin


class QdrantClientWrapper(LoggerMixin):
    """
    Wrapper around Qdrant client for vector store operations.

    Provides high-level methods for common vector operations
    and handles connection management.
    """

    def __init__(self) -> None:
        """Initialize Qdrant client with configuration."""
        settings = get_settings()
        self.host = settings.qdrant.qdrant_host
        self.port = settings.qdrant.qdrant_port
        self.api_key = settings.qdrant.qdrant_api_key
        self.vector_size = settings.qdrant.qdrant_vector_size
        self.distance_metric = getattr(Distance, settings.qdrant.qdrant_distance_metric.upper())

        # Initialize async client
        # For local connections, use HTTP without SSL
        use_https = self.host not in ["localhost", "127.0.0.1", "qdrant"]

        self.client = AsyncQdrantClient(
            host=self.host,
            port=self.port,
            api_key=self.api_key if self.api_key else None,
            timeout=30,
            https=use_https,
            prefer_grpc=False,  # Use REST API for better compatibility
        )

        self.logger.info(
            "qdrant_client_initialized",
            host=self.host,
            port=self.port,
            vector_size=self.vector_size,
        )

    async def close(self) -> None:
        """Close the Qdrant client connection."""
        await self.client.close()
        self.logger.info("qdrant_client_closed")

    async def __aenter__(self) -> "QdrantClientWrapper":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def ensure_collection(
        self, collection_name: str, vector_size: int | None = None
    ) -> None:
        """
        Ensure a collection exists, create if it doesn't.

        Args:
            collection_name: Name of the collection
            vector_size: Vector dimension size (defaults to config value)

        Raises:
            VectorStoreError: If collection creation fails
        """
        vector_size = vector_size or self.vector_size

        try:
            # Check if collection exists
            collections = await self.client.get_collections()
            exists = any(c.name == collection_name for c in collections.collections)

            if not exists:
                self.logger.info(
                    "creating_collection",
                    collection_name=collection_name,
                    vector_size=vector_size,
                )

                await self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=self.distance_metric,
                    ),
                )

                self.logger.info("collection_created", collection_name=collection_name)
            else:
                self.logger.debug("collection_exists", collection_name=collection_name)

        except Exception as e:
            self.logger.error(
                "collection_creation_failed",
                collection_name=collection_name,
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to ensure collection: {collection_name}",
                details={"error": str(e), "collection_name": collection_name},
            ) from e

    async def upsert_point(
        self,
        collection_name: str,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        """
        Upsert a single point into a collection.

        Args:
            collection_name: Name of the collection
            point_id: Unique point identifier
            vector: Embedding vector
            payload: Metadata payload

        Raises:
            VectorStoreError: If upsert fails
        """
        try:
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )

            await self.client.upsert(
                collection_name=collection_name,
                points=[point],
            )

            self.logger.debug(
                "point_upserted",
                collection_name=collection_name,
                point_id=point_id,
            )

        except Exception as e:
            self.logger.error(
                "point_upsert_failed",
                collection_name=collection_name,
                point_id=point_id,
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to upsert point: {point_id}",
                details={"error": str(e), "point_id": point_id},
            ) from e

    async def upsert_points(
        self,
        collection_name: str,
        points: list[tuple[str, list[float], dict[str, Any]]],
    ) -> None:
        """
        Upsert multiple points into a collection.

        Args:
            collection_name: Name of the collection
            points: List of (point_id, vector, payload) tuples

        Raises:
            VectorStoreError: If upsert fails
        """
        try:
            point_structs = [
                PointStruct(id=point_id, vector=vector, payload=payload)
                for point_id, vector, payload in points
            ]

            await self.client.upsert(
                collection_name=collection_name,
                points=point_structs,
            )

            self.logger.info(
                "batch_upserted",
                collection_name=collection_name,
                num_points=len(points),
            )

        except Exception as e:
            self.logger.error(
                "batch_upsert_failed",
                collection_name=collection_name,
                num_points=len(points),
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to upsert {len(points)} points",
                details={"error": str(e), "num_points": len(points)},
            ) from e

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
        filter_conditions: Filter | None = None,
    ) -> list[Any]:
        """
        Search for similar vectors in a collection.

        Args:
            collection_name: Name of the collection
            query_vector: Query embedding
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filter_conditions: Optional filter conditions

        Returns:
            List of search results

        Raises:
            VectorStoreError: If search fails
        """
        try:
            results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=filter_conditions,
            )

            self.logger.debug(
                "search_completed",
                collection_name=collection_name,
                num_results=len(results),
            )

            return results

        except Exception as e:
            self.logger.error(
                "search_failed",
                collection_name=collection_name,
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to search collection: {collection_name}",
                details={"error": str(e)},
            ) from e

    async def get_point(
        self, collection_name: str, point_id: str
    ) -> dict[str, Any] | None:
        """
        Retrieve a point by ID.

        Args:
            collection_name: Name of the collection
            point_id: Point identifier

        Returns:
            Point data or None if not found

        Raises:
            VectorStoreError: If retrieval fails
        """
        try:
            points = await self.client.retrieve(
                collection_name=collection_name,
                ids=[point_id],
            )

            if not points:
                return None

            point = points[0]
            return {
                "id": point.id,
                "vector": point.vector,
                "payload": point.payload,
            }

        except Exception as e:
            self.logger.error(
                "get_point_failed",
                collection_name=collection_name,
                point_id=point_id,
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to get point: {point_id}",
                details={"error": str(e)},
            ) from e

    async def delete_point(self, collection_name: str, point_id: str) -> bool:
        """
        Delete a point by ID.

        Args:
            collection_name: Name of the collection
            point_id: Point identifier

        Returns:
            True if deleted, False if not found

        Raises:
            VectorStoreError: If deletion fails
        """
        try:
            await self.client.delete(
                collection_name=collection_name,
                points_selector=[point_id],
            )

            self.logger.info(
                "point_deleted",
                collection_name=collection_name,
                point_id=point_id,
            )

            return True

        except Exception as e:
            self.logger.error(
                "delete_point_failed",
                collection_name=collection_name,
                point_id=point_id,
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to delete point: {point_id}",
                details={"error": str(e)},
            ) from e

    async def delete_points_by_filter(
        self, collection_name: str, filter_conditions: Filter
    ) -> int:
        """
        Delete points matching filter conditions.

        Args:
            collection_name: Name of the collection
            filter_conditions: Filter to match points

        Returns:
            Number of points deleted

        Raises:
            VectorStoreError: If deletion fails
        """
        try:
            # First, scroll to get matching points
            scroll_result = await self.client.scroll(
                collection_name=collection_name,
                scroll_filter=filter_conditions,
                limit=10000,
            )

            point_ids = [point.id for point in scroll_result[0]]

            if not point_ids:
                return 0

            # Delete the points
            await self.client.delete(
                collection_name=collection_name,
                points_selector=point_ids,
            )

            self.logger.info(
                "points_deleted_by_filter",
                collection_name=collection_name,
                num_deleted=len(point_ids),
            )

            return len(point_ids)

        except Exception as e:
            self.logger.error(
                "delete_by_filter_failed",
                collection_name=collection_name,
                error=str(e),
            )
            raise VectorStoreError(
                "Failed to delete points by filter",
                details={"error": str(e)},
            ) from e

    async def count_points(
        self, collection_name: str, filter_conditions: Filter | None = None
    ) -> int:
        """
        Count points in a collection.

        Args:
            collection_name: Name of the collection
            filter_conditions: Optional filter conditions

        Returns:
            Number of points

        Raises:
            VectorStoreError: If count fails
        """
        try:
            result = await self.client.count(
                collection_name=collection_name,
                count_filter=filter_conditions,
                exact=True,
            )

            return result.count

        except Exception as e:
            self.logger.error(
                "count_failed",
                collection_name=collection_name,
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to count points in {collection_name}",
                details={"error": str(e)},
            ) from e
