"""
Domain repository interfaces - Contracts for data access.
"""

from src.domain.repositories.conversation_repository import IConversationRepository
from src.domain.repositories.document_repository import IDocumentRepository
from src.domain.repositories.graph_repository import IGraphRepository
from src.domain.repositories.memory_repository import IMemoryRepository

__all__ = [
    "IMemoryRepository",
    "IDocumentRepository",
    "IConversationRepository",
    "IGraphRepository",
]
