"""
Dependency injection for FastAPI endpoints.
"""

from functools import lru_cache

from src.application.use_cases.chat_use_case import ChatUseCase
from src.application.use_cases.document_use_cases import (
    DeleteDocumentUseCase,
    SearchDocumentsUseCase,
    UploadDocumentUseCase,
)
from src.application.use_cases.entity_extraction_use_case import (
    EntityExtractionUseCase,
)
from src.application.use_cases.memory_use_cases import (
    CreateMemoryUseCase,
    DeleteMemoryUseCase,
    GetMemoryByIdUseCase,
    SearchMemoriesUseCase,
)
from src.application.use_cases.rag_use_case import RAGUseCase
from src.infrastructure.database.conversation_repository_impl import (
    PostgreSQLConversationRepository,
)
from src.infrastructure.embeddings.embedding_service import EmbeddingService
from src.infrastructure.graph_db.graph_repository_impl import Neo4jGraphRepository
from src.infrastructure.llm.llm_service import LLMService
from src.infrastructure.llm.openrouter_client import OpenRouterClient
from src.infrastructure.document_processing.document_processor import DocumentProcessor
from src.infrastructure.vector_store.document_repository_impl import (
    QdrantDocumentRepository,
)
from src.infrastructure.vector_store.memory_repository_impl import QdrantMemoryRepository


# Infrastructure Singletons


@lru_cache
def get_openrouter_client() -> OpenRouterClient:
    """Get or create OpenRouter client singleton."""
    return OpenRouterClient()


@lru_cache
def get_llm_service() -> LLMService:
    """Get or create LLM service singleton."""
    client = get_openrouter_client()
    return LLMService(client=client)


@lru_cache
def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service singleton."""
    client = get_openrouter_client()
    return EmbeddingService(client=client)


@lru_cache
def get_memory_repository() -> QdrantMemoryRepository:
    """Get or create memory repository singleton."""
    return QdrantMemoryRepository()


@lru_cache
def get_document_repository() -> QdrantDocumentRepository:
    """Get or create document repository singleton."""
    return QdrantDocumentRepository()


@lru_cache
def get_conversation_repository() -> PostgreSQLConversationRepository:
    """Get or create conversation repository singleton."""
    return PostgreSQLConversationRepository()


@lru_cache
def get_graph_repository() -> Neo4jGraphRepository:
    """Get or create graph repository singleton."""
    return Neo4jGraphRepository()


@lru_cache
def get_document_processor() -> DocumentProcessor:
    """Get or create document processor singleton."""
    return DocumentProcessor()


# Use Case Dependencies


def get_create_memory_use_case() -> CreateMemoryUseCase:
    """Get create memory use case with dependencies."""
    return CreateMemoryUseCase(
        memory_repo=get_memory_repository(),
        embedding_service=get_embedding_service(),
    )


def get_search_memories_use_case() -> SearchMemoriesUseCase:
    """Get search memories use case with dependencies."""
    return SearchMemoriesUseCase(
        memory_repo=get_memory_repository(),
        embedding_service=get_embedding_service(),
    )


def get_memory_by_id_use_case() -> GetMemoryByIdUseCase:
    """Get memory by ID use case with dependencies."""
    return GetMemoryByIdUseCase(
        memory_repo=get_memory_repository(),
    )


def get_delete_memory_use_case() -> DeleteMemoryUseCase:
    """Get delete memory use case with dependencies."""
    return DeleteMemoryUseCase(
        memory_repo=get_memory_repository(),
    )


def get_rag_use_case() -> RAGUseCase:
    """Get RAG use case with dependencies."""
    return RAGUseCase(
        memory_repo=get_memory_repository(),
        document_repo=get_document_repository(),
        embedding_service=get_embedding_service(),
        llm_service=get_llm_service(),
        graph_repo=get_graph_repository(),
    )


def get_entity_extraction_use_case() -> EntityExtractionUseCase:
    """Get entity extraction use case with dependencies."""
    return EntityExtractionUseCase(
        graph_repo=get_graph_repository(),
        llm_service=get_llm_service(),
    )


def get_chat_use_case() -> ChatUseCase:
    """Get chat use case with dependencies."""
    return ChatUseCase(
        conversation_repo=get_conversation_repository(),
        rag_use_case=get_rag_use_case(),
        create_memory_use_case=get_create_memory_use_case(),
        entity_extraction_use_case=get_entity_extraction_use_case(),
        llm_service=get_llm_service(),
    )


def get_upload_document_use_case() -> UploadDocumentUseCase:
    """Get upload document use case with dependencies."""
    return UploadDocumentUseCase(
        document_repo=get_document_repository(),
        embedding_service=get_embedding_service(),
        document_processor=get_document_processor(),
        entity_extraction_use_case=get_entity_extraction_use_case(),
    )


def get_search_documents_use_case() -> SearchDocumentsUseCase:
    """Get search documents use case with dependencies."""
    return SearchDocumentsUseCase(
        document_repo=get_document_repository(),
        embedding_service=get_embedding_service(),
    )


def get_delete_document_use_case() -> DeleteDocumentUseCase:
    """Get delete document use case with dependencies."""
    return DeleteDocumentUseCase(
        document_repo=get_document_repository(),
    )
