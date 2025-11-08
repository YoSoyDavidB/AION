"""
Application DTOs - Data Transfer Objects for use cases.
"""

from src.application.dtos.chat_dto import ChatRequest, ChatResponse
from src.application.dtos.memory_dto import (
    MemoryCreateRequest,
    MemoryResponse,
    MemorySearchRequest,
)
from src.application.dtos.rag_dto import RAGContext, RAGRequest, RAGResponse

__all__ = [
    # Chat
    "ChatRequest",
    "ChatResponse",
    # Memory
    "MemoryCreateRequest",
    "MemoryResponse",
    "MemorySearchRequest",
    # RAG
    "RAGRequest",
    "RAGResponse",
    "RAGContext",
]
