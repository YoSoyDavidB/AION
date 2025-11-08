"""
Document repository interface - Contract for document storage operations.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.document import Document


class IDocumentRepository(ABC):
    """
    Interface for document repository operations.

    This defines the contract for document chunk storage and retrieval.
    """

    @abstractmethod
    async def create(self, document: Document) -> Document:
        """
        Create a new document chunk.

        Args:
            document: Document entity to create

        Returns:
            Created document with any generated fields

        Raises:
            VectorStoreError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, doc_id: UUID) -> Document | None:
        """
        Retrieve a document by ID.

        Args:
            doc_id: Document identifier

        Returns:
            Document if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_chunk_id(self, chunk_id: str) -> Document | None:
        """
        Retrieve a document by chunk ID.

        Args:
            chunk_id: Chunk identifier (hash)

        Returns:
            Document if found, None otherwise
        """
        pass

    @abstractmethod
    async def update(self, document: Document) -> Document:
        """
        Update an existing document.

        Args:
            document: Document entity with updated fields

        Returns:
            Updated document

        Raises:
            EntityNotFoundError: If document doesn't exist
        """
        pass

    @abstractmethod
    async def delete(self, doc_id: UUID) -> bool:
        """
        Delete a document.

        Args:
            doc_id: Document identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def delete_by_path(self, path: str) -> int:
        """
        Delete all document chunks for a specific file path.

        Args:
            path: File path

        Returns:
            Number of chunks deleted
        """
        pass

    @abstractmethod
    async def search_similar(
        self,
        query_embedding: list[float],
        user_id: str | None = None,
        limit: int = 10,
        min_score: float = 0.7,
        tags: list[str] | None = None,
        source_type: str | None = None,
    ) -> list[tuple[Document, float]]:
        """
        Search for similar documents using vector similarity.

        Args:
            query_embedding: Query vector
            user_id: Filter by user ID (optional)
            limit: Maximum number of results
            min_score: Minimum similarity score
            tags: Filter by tags (optional)
            source_type: Filter by source type (optional)

        Returns:
            List of (Document, similarity_score) tuples
        """
        pass

    @abstractmethod
    async def get_by_path(self, path: str) -> list[Document]:
        """
        Get all document chunks for a specific file path.

        Args:
            path: File path

        Returns:
            List of document chunks
        """
        pass

    @abstractmethod
    async def get_by_tags(
        self, tags: list[str], limit: int = 100
    ) -> list[Document]:
        """
        Get documents by tags.

        Args:
            tags: Tags to filter by
            limit: Maximum number of results

        Returns:
            List of documents
        """
        pass

    @abstractmethod
    async def bulk_create(self, documents: list[Document]) -> list[Document]:
        """
        Create multiple documents at once.

        Args:
            documents: List of documents to create

        Returns:
            List of created documents
        """
        pass

    @abstractmethod
    async def bulk_upsert(self, documents: list[Document]) -> list[Document]:
        """
        Upsert multiple documents (create or update based on chunk_id).

        Args:
            documents: List of documents to upsert

        Returns:
            List of upserted documents
        """
        pass

    @abstractmethod
    async def search_by_text(
        self, query: str, limit: int = 10
    ) -> list[Document]:
        """
        Search documents by text content.

        Args:
            query: Text query
            limit: Maximum number of results

        Returns:
            List of matching documents
        """
        pass

    @abstractmethod
    async def count(
        self, source_type: str | None = None, path: str | None = None
    ) -> int:
        """
        Count documents, optionally filtered.

        Args:
            source_type: Filter by source type (optional)
            path: Filter by path (optional)

        Returns:
            Number of documents
        """
        pass

    @abstractmethod
    async def get_all_paths(self, source_type: str | None = None) -> list[str]:
        """
        Get all unique file paths in the knowledge base.

        Args:
            source_type: Filter by source type (optional)

        Returns:
            List of file paths
        """
        pass

    @abstractmethod
    async def get_recent_updates(
        self, days: int = 7, limit: int = 100
    ) -> list[Document]:
        """
        Get recently updated documents.

        Args:
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of recent documents
        """
        pass

    @abstractmethod
    async def get_by_hash(self, file_hash: str, user_id: str) -> list[Document]:
        """
        Get documents by file hash for deduplication.

        Args:
            file_hash: Hash of the file content
            user_id: User ID for filtering

        Returns:
            List of documents with matching hash
        """
        pass

    @abstractmethod
    async def delete_by_doc_id(self, doc_id: UUID, user_id: str) -> int:
        """
        Delete all chunks of a document by doc_id.

        Args:
            doc_id: Document identifier
            user_id: User ID for authorization

        Returns:
            Number of chunks deleted
        """
        pass
