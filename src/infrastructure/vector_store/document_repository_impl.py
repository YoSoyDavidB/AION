"""
Qdrant implementation of Document repository.
"""

from datetime import datetime, timedelta
from uuid import UUID

from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue

from src.config.settings import get_settings
from src.domain.entities.document import Document
from src.domain.repositories.document_repository import IDocumentRepository
from src.infrastructure.vector_store.qdrant_client import QdrantClientWrapper
from src.shared.exceptions import EntityNotFoundError, VectorStoreError
from src.shared.logging import LoggerMixin


class QdrantDocumentRepository(IDocumentRepository, LoggerMixin):
    """
    Qdrant implementation of Document repository.

    Stores document chunks as vector embeddings with metadata in Qdrant.
    """

    def __init__(self, qdrant_client: QdrantClientWrapper | None = None) -> None:
        """
        Initialize repository.

        Args:
            qdrant_client: Qdrant client instance (optional)
        """
        settings = get_settings()
        self.client = qdrant_client or QdrantClientWrapper()
        self.collection_name = settings.qdrant.qdrant_collection_documents

        self.logger.info(
            "document_repository_initialized",
            collection=self.collection_name,
        )

    async def initialize(self) -> None:
        """Initialize the collection if it doesn't exist."""
        await self.client.ensure_collection(self.collection_name)

    def _document_to_payload(self, document: Document) -> dict:
        """Convert Document entity to Qdrant payload."""
        return {
            "doc_id": str(document.doc_id),
            "user_id": document.user_id,
            "chunk_id": document.chunk_id,
            "path": document.path,
            "title": document.title,
            "content": document.content,
            "heading": document.heading,
            "tags": document.tags,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
            "language": document.language,
            "source_type": document.source_type,
            "metadata": document.metadata,
            "char_count": document.char_count,
            "token_count": document.token_count,
        }

    def _payload_to_document(self, payload: dict, vector: list[float]) -> Document:
        """Convert Qdrant payload to Document entity."""
        return Document(
            doc_id=UUID(payload["doc_id"]),
            user_id=payload["user_id"],
            chunk_id=payload["chunk_id"],
            path=payload["path"],
            title=payload.get("title", ""),
            content=payload["content"],
            heading=payload.get("heading"),
            tags=payload.get("tags", []),
            created_at=datetime.fromisoformat(payload["created_at"]),
            updated_at=datetime.fromisoformat(payload["updated_at"]),
            language=payload.get("language", "en"),
            embedding=vector,
            source_type=payload.get("source_type", "obsidian"),
            metadata=payload.get("metadata", {}),
            char_count=payload.get("char_count", 0),
            token_count=payload.get("token_count", 0),
        )

    async def create(self, document: Document) -> Document:
        """Create a new document."""
        if document.embedding is None:
            raise VectorStoreError(
                "Document must have an embedding before storage",
                details={"doc_id": str(document.doc_id)},
            )

        try:
            # Calculate metrics if not set
            if document.char_count == 0:
                document.calculate_metrics()

            payload = self._document_to_payload(document)
            # Use chunk_id (hash) as unique point_id
            await self.client.upsert_point(
                collection_name=self.collection_name,
                point_id=document.chunk_id,
                vector=document.embedding,
                payload=payload,
            )

            self.logger.info(
                "document_created",
                doc_id=str(document.doc_id),
                path=document.path,
            )

            return document

        except Exception as e:
            self.logger.error(
                "document_creation_failed",
                doc_id=str(document.doc_id),
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to create document: {str(e)}",
                details={"doc_id": str(document.doc_id)},
            ) from e

    async def get_by_id(self, doc_id: UUID) -> Document | None:
        """Retrieve a document by ID."""
        try:
            point = await self.client.get_point(
                collection_name=self.collection_name,
                point_id=str(doc_id),
            )

            if point is None:
                return None

            document = self._payload_to_document(point["payload"], point["vector"])
            return document

        except Exception as e:
            self.logger.error(
                "document_retrieval_failed",
                doc_id=str(doc_id),
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to retrieve document: {str(e)}",
                details={"doc_id": str(doc_id)},
            ) from e

    async def get_by_chunk_id(self, chunk_id: str) -> Document | None:
        """Retrieve a document by chunk ID."""
        try:
            filter_conditions = Filter(
                must=[
                    FieldCondition(
                        key="chunk_id",
                        match=MatchValue(value=chunk_id),
                    )
                ]
            )

            results, _ = await self.client.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_conditions,
                limit=1,
                with_vectors=True,
            )

            if not results:
                return None

            return self._payload_to_document(results[0].payload, results[0].vector)

        except Exception as e:
            self.logger.error(
                "get_by_chunk_id_failed",
                chunk_id=chunk_id,
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to get document by chunk_id: {str(e)}"
            ) from e

    async def update(self, document: Document) -> Document:
        """Update an existing document."""
        existing = await self.get_by_id(document.doc_id)
        if existing is None:
            raise EntityNotFoundError("Document", str(document.doc_id))

        if document.embedding is None:
            raise VectorStoreError(
                "Document must have an embedding for update",
                details={"doc_id": str(document.doc_id)},
            )

        try:
            if document.char_count == 0:
                document.calculate_metrics()

            payload = self._document_to_payload(document)
            # Use chunk_id (hash) as unique point_id
            await self.client.upsert_point(
                collection_name=self.collection_name,
                point_id=document.chunk_id,
                vector=document.embedding,
                payload=payload,
            )

            self.logger.info("document_updated", doc_id=str(document.doc_id))

            return document

        except Exception as e:
            self.logger.error(
                "document_update_failed",
                doc_id=str(document.doc_id),
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to update document: {str(e)}"
            ) from e

    async def delete(self, doc_id: UUID) -> bool:
        """Delete a document."""
        try:
            deleted = await self.client.delete_point(
                collection_name=self.collection_name,
                point_id=str(doc_id),
            )

            if deleted:
                self.logger.info("document_deleted", doc_id=str(doc_id))

            return deleted

        except Exception as e:
            self.logger.error(
                "document_deletion_failed",
                doc_id=str(doc_id),
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to delete document: {str(e)}"
            ) from e

    async def delete_by_path(self, path: str) -> int:
        """Delete all document chunks for a specific file path."""
        try:
            filter_conditions = Filter(
                must=[
                    FieldCondition(
                        key="path",
                        match=MatchValue(value=path),
                    )
                ]
            )

            deleted_count = await self.client.delete_points_by_filter(
                self.collection_name, filter_conditions
            )

            self.logger.info(
                "documents_deleted_by_path",
                path=path,
                count=deleted_count,
            )

            return deleted_count

        except Exception as e:
            self.logger.error(
                "delete_by_path_failed",
                path=path,
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to delete documents by path: {str(e)}"
            ) from e

    async def search_similar(
        self,
        query_embedding: list[float],
        user_id: str | None = None,
        limit: int = 10,
        min_score: float = 0.7,
        tags: list[str] | None = None,
        source_type: str | None = None,
    ) -> list[tuple[Document, float]]:
        """Search for similar documents."""
        try:
            # Build filter conditions
            must_conditions = []

            if user_id:
                must_conditions.append(
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id),
                    )
                )

            if tags:
                must_conditions.append(
                    FieldCondition(
                        key="tags",
                        match=MatchAny(any=tags),
                    )
                )

            if source_type:
                must_conditions.append(
                    FieldCondition(
                        key="source_type",
                        match=MatchValue(value=source_type),
                    )
                )

            filter_conditions = Filter(must=must_conditions) if must_conditions else None

            results = await self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=min_score,
                filter_conditions=filter_conditions,
            )

            documents_with_scores = []
            for result in results:
                document = self._payload_to_document(result.payload, result.vector)
                documents_with_scores.append((document, result.score))

            self.logger.info(
                "documents_searched",
                num_results=len(documents_with_scores),
                min_score=min_score,
            )

            return documents_with_scores

        except Exception as e:
            self.logger.error("document_search_failed", error=str(e))
            raise VectorStoreError(
                f"Failed to search documents: {str(e)}"
            ) from e

    async def get_by_path(self, path: str) -> list[Document]:
        """Get all document chunks for a specific file path."""
        try:
            filter_conditions = Filter(
                must=[
                    FieldCondition(
                        key="path",
                        match=MatchValue(value=path),
                    )
                ]
            )

            results, _ = await self.client.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_conditions,
                limit=1000,
                with_vectors=True,
            )

            documents = [
                self._payload_to_document(point.payload, point.vector)
                for point in results
            ]

            return documents

        except Exception as e:
            self.logger.error("get_by_path_failed", path=path, error=str(e))
            raise VectorStoreError(
                f"Failed to get documents by path: {str(e)}"
            ) from e

    async def get_by_tags(
        self, tags: list[str], limit: int = 100
    ) -> list[Document]:
        """Get documents by tags."""
        try:
            filter_conditions = Filter(
                must=[
                    FieldCondition(
                        key="tags",
                        match=MatchAny(any=tags),
                    )
                ]
            )

            results, _ = await self.client.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_conditions,
                limit=limit,
                with_vectors=True,
            )

            documents = [
                self._payload_to_document(point.payload, point.vector)
                for point in results
            ]

            return documents

        except Exception as e:
            self.logger.error("get_by_tags_failed", error=str(e))
            raise VectorStoreError(
                f"Failed to get documents by tags: {str(e)}"
            ) from e

    async def bulk_create(self, documents: list[Document]) -> list[Document]:
        """Create multiple documents at once."""
        try:
            points = []
            for document in documents:
                if document.embedding is None:
                    raise VectorStoreError(
                        "All documents must have embeddings",
                        details={"doc_id": str(document.doc_id)},
                    )

                if document.char_count == 0:
                    document.calculate_metrics()

                payload = self._document_to_payload(document)
                points.append((str(document.doc_id), document.embedding, payload))

            await self.client.upsert_points(self.collection_name, points)

            self.logger.info("bulk_documents_created", count=len(documents))

            return documents

        except Exception as e:
            self.logger.error("bulk_create_failed", error=str(e))
            raise VectorStoreError(
                f"Failed to bulk create documents: {str(e)}"
            ) from e

    async def bulk_upsert(self, documents: list[Document]) -> list[Document]:
        """Upsert multiple documents."""
        # In Qdrant, upsert is the same as create (it updates if exists)
        return await self.bulk_create(documents)

    async def search_by_text(self, query: str, limit: int = 10) -> list[Document]:
        """Search documents by text content."""
        # Would need embedding service integration
        self.logger.warning("text_search_not_fully_implemented")
        return []

    async def count(
        self, source_type: str | None = None, path: str | None = None
    ) -> int:
        """Count documents, optionally filtered."""
        try:
            must_conditions = []

            if source_type:
                must_conditions.append(
                    FieldCondition(
                        key="source_type",
                        match=MatchValue(value=source_type),
                    )
                )

            if path:
                must_conditions.append(
                    FieldCondition(
                        key="path",
                        match=MatchValue(value=path),
                    )
                )

            filter_conditions = Filter(must=must_conditions) if must_conditions else None

            count = await self.client.count_points(
                self.collection_name, filter_conditions
            )

            return count

        except Exception as e:
            self.logger.error("count_failed", error=str(e))
            raise VectorStoreError(f"Failed to count documents: {str(e)}") from e

    async def get_all_paths(self, source_type: str | None = None) -> list[str]:
        """Get all unique file paths."""
        try:
            filter_conditions = None
            if source_type:
                filter_conditions = Filter(
                    must=[
                        FieldCondition(
                            key="source_type",
                            match=MatchValue(value=source_type),
                        )
                    ]
                )

            results, _ = await self.client.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_conditions,
                limit=10000,
                with_payload=["path"],
                with_vectors=False,
            )

            paths = list(set(point.payload["path"] for point in results))
            return sorted(paths)

        except Exception as e:
            self.logger.error("get_all_paths_failed", error=str(e))
            raise VectorStoreError(
                f"Failed to get all paths: {str(e)}"
            ) from e

    async def get_recent_updates(
        self, days: int = 7, limit: int = 100
    ) -> list[Document]:
        """Get recently updated documents."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            results, _ = await self.client.client.scroll(
                collection_name=self.collection_name,
                limit=limit * 2,
                with_vectors=True,
            )

            documents = [
                self._payload_to_document(point.payload, point.vector)
                for point in results
            ]

            # Filter by date and sort
            recent_docs = [
                doc for doc in documents if doc.updated_at >= cutoff_date
            ]
            recent_docs.sort(key=lambda d: d.updated_at, reverse=True)

            return recent_docs[:limit]

        except Exception as e:
            self.logger.error("get_recent_updates_failed", error=str(e))
            raise VectorStoreError(
                f"Failed to get recent updates: {str(e)}"
            ) from e

    async def get_by_hash(self, file_hash: str, user_id: str) -> list[Document]:
        """Get documents by file hash for deduplication."""
        try:
            filter_conditions = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id),
                    ),
                    FieldCondition(
                        key="metadata.file_hash",
                        match=MatchValue(value=file_hash),
                    ),
                ]
            )

            results, _ = await self.client.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_conditions,
                limit=1000,
                with_vectors=True,
            )

            documents = [
                self._payload_to_document(point.payload, point.vector)
                for point in results
            ]

            self.logger.info(
                "documents_found_by_hash",
                file_hash=file_hash,
                count=len(documents),
            )

            return documents

        except Exception as e:
            self.logger.error("get_by_hash_failed", file_hash=file_hash, error=str(e))
            raise VectorStoreError(
                f"Failed to get documents by hash: {str(e)}"
            ) from e

    async def delete_by_doc_id(self, doc_id: UUID, user_id: str) -> int:
        """Delete all chunks of a document by doc_id."""
        try:
            filter_conditions = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id),
                    ),
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=str(doc_id)),
                    ),
                ]
            )

            deleted = await self.client.delete_points_by_filter(
                collection_name=self.collection_name,
                filter_conditions=filter_conditions,
            )

            self.logger.info(
                "document_deleted_by_id",
                doc_id=str(doc_id),
                chunks_deleted=deleted,
            )

            return deleted

        except Exception as e:
            self.logger.error(
                "delete_by_doc_id_failed",
                doc_id=str(doc_id),
                error=str(e),
            )
            raise VectorStoreError(
                f"Failed to delete document by ID: {str(e)}"
            ) from e
