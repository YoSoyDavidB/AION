"""
Domain entities - Core business objects.
"""

from src.domain.entities.conversation import (
    Conversation,
    ConversationStatus,
    Message,
    MessageRole,
)
from src.domain.entities.document import Document, SourceType
from src.domain.entities.graph_entity import (
    EntitySearchResult,
    EntityType,
    GraphEntity,
    GraphRelationship,
    RelationType,
)
from src.domain.entities.memory import Memory, MemoryType, SensitivityLevel
from src.domain.entities.oauth_token import OAuthProvider, OAuthToken
from src.domain.entities.calendar_event import CalendarEvent
from src.domain.entities.email import Email, EmailAddress

__all__ = [
    # Memory
    "Memory",
    "MemoryType",
    "SensitivityLevel",
    # Document
    "Document",
    "SourceType",
    # Conversation
    "Conversation",
    "ConversationStatus",
    "Message",
    "MessageRole",
    # Graph
    "GraphEntity",
    "GraphRelationship",
    "EntityType",
    "RelationType",
    "EntitySearchResult",
    # OAuth & Integrations
    "OAuthToken",
    "OAuthProvider",
    "CalendarEvent",
    "Email",
    "EmailAddress",
]
