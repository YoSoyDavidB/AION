"""
Conversation repository interface - Contract for conversation storage operations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.domain.entities.conversation import Conversation, ConversationStatus


class IConversationRepository(ABC):
    """
    Interface for conversation repository operations.

    This defines the contract for conversation and message storage.
    """

    @abstractmethod
    async def create(self, conversation: Conversation) -> Conversation:
        """
        Create a new conversation.

        Args:
            conversation: Conversation entity to create

        Returns:
            Created conversation

        Raises:
            DatabaseError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        """
        Retrieve a conversation by ID.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Conversation if found, None otherwise
        """
        pass

    @abstractmethod
    async def update(self, conversation: Conversation) -> Conversation:
        """
        Update an existing conversation.

        Args:
            conversation: Conversation entity with updated fields

        Returns:
            Updated conversation

        Raises:
            EntityNotFoundError: If conversation doesn't exist
        """
        pass

    @abstractmethod
    async def delete(self, conversation_id: UUID) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def get_by_user(
        self,
        user_id: str,
        status: ConversationStatus | None = None,
        limit: int = 100,
    ) -> list[Conversation]:
        """
        Get conversations for a specific user.

        Args:
            user_id: User identifier
            status: Filter by status (optional)
            limit: Maximum number of results

        Returns:
            List of conversations
        """
        pass

    @abstractmethod
    async def get_active_conversation(
        self, user_id: str
    ) -> Conversation | None:
        """
        Get the active conversation for a user.

        Args:
            user_id: User identifier

        Returns:
            Active conversation if exists, None otherwise
        """
        pass

    @abstractmethod
    async def get_recent(
        self,
        user_id: str | None = None,
        days: int = 7,
        limit: int = 10,
    ) -> list[Conversation]:
        """
        Get recent conversations.

        Args:
            user_id: Filter by user (optional)
            days: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of recent conversations
        """
        pass

    @abstractmethod
    async def search_by_content(
        self, query: str, user_id: str | None = None, limit: int = 10
    ) -> list[Conversation]:
        """
        Search conversations by message content.

        Args:
            query: Search query
            user_id: Filter by user (optional)
            limit: Maximum number of results

        Returns:
            List of matching conversations
        """
        pass

    @abstractmethod
    async def count(
        self,
        user_id: str | None = None,
        status: ConversationStatus | None = None,
    ) -> int:
        """
        Count conversations, optionally filtered.

        Args:
            user_id: Filter by user (optional)
            status: Filter by status (optional)

        Returns:
            Number of conversations
        """
        pass

    @abstractmethod
    async def archive_old_conversations(
        self, days_threshold: int = 30
    ) -> int:
        """
        Archive conversations older than threshold.

        Args:
            days_threshold: Number of days to consider old

        Returns:
            Number of conversations archived
        """
        pass

    @abstractmethod
    async def get_conversation_stats(
        self, user_id: str
    ) -> dict[str, int]:
        """
        Get conversation statistics for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with stats (total, active, completed, etc.)
        """
        pass
