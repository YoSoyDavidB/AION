"""
Conversation and Message entities.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class MessageRole(str, Enum):
    """Message roles in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """
    Represents a single message in a conversation.
    """

    message_id: UUID = Field(default_factory=uuid4, description="Message identifier")
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    token_count: int = Field(default=0, ge=0, description="Approximate token count")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Ensure content is not empty."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Message content cannot be empty")
        return stripped

    def calculate_tokens(self) -> None:
        """Calculate approximate token count."""
        # Rough approximation: 1 token ≈ 4 characters
        self.token_count = len(self.content) // 4

    model_config = {"json_schema_extra": {"example": {
        "message_id": "550e8400-e29b-41d4-a716-446655440000",
        "role": "user",
        "content": "What are Python best practices?",
        "timestamp": "2024-11-07T10:30:00Z",
    }}}


class ConversationStatus(str, Enum):
    """Conversation status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Conversation(BaseModel):
    """
    Represents a conversation session with the user.

    Conversations contain multiple messages and track context,
    memories extracted, and relevant metadata.
    """

    conversation_id: UUID = Field(
        default_factory=uuid4, description="Conversation identifier"
    )
    user_id: str = Field(..., description="User identifier")
    messages: list[Message] = Field(default_factory=list, description="Conversation messages")
    status: ConversationStatus = Field(
        default=ConversationStatus.ACTIVE, description="Conversation status"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Conversation start time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update time"
    )
    memories_extracted: list[UUID] = Field(
        default_factory=list, description="Memory IDs extracted from this conversation"
    )
    summary: str | None = Field(default=None, description="Conversation summary")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    total_tokens: int = Field(default=0, ge=0, description="Total tokens in conversation")

    def add_message(self, role: MessageRole, content: str) -> Message:
        """
        Add a new message to the conversation.

        Args:
            role: Message role
            content: Message content

        Returns:
            Created message
        """
        message = Message(role=role, content=content)
        message.calculate_tokens()
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        self.total_tokens += message.token_count
        return message

    def get_messages_by_role(self, role: MessageRole) -> list[Message]:
        """
        Get all messages with a specific role.

        Args:
            role: Message role to filter by

        Returns:
            List of messages
        """
        return [msg for msg in self.messages if msg.role == role]

    def get_last_n_messages(self, n: int) -> list[Message]:
        """
        Get the last N messages.

        Args:
            n: Number of messages to retrieve

        Returns:
            List of most recent messages
        """
        return self.messages[-n:] if n > 0 else []

    def mark_completed(self) -> None:
        """Mark conversation as completed."""
        self.status = ConversationStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def archive(self) -> None:
        """Archive the conversation."""
        self.status = ConversationStatus.ARCHIVED
        self.updated_at = datetime.utcnow()

    def add_extracted_memory(self, memory_id: UUID) -> None:
        """
        Add a memory ID that was extracted from this conversation.

        Args:
            memory_id: Memory identifier
        """
        if memory_id not in self.memories_extracted:
            self.memories_extracted.append(memory_id)
            self.updated_at = datetime.utcnow()

    def get_context_window(self, max_tokens: int = 4000) -> list[Message]:
        """
        Get messages that fit within a token limit.

        Args:
            max_tokens: Maximum tokens for context window

        Returns:
            List of messages within token limit
        """
        messages_in_window: list[Message] = []
        current_tokens = 0

        # Start from most recent messages
        for message in reversed(self.messages):
            if current_tokens + message.token_count > max_tokens:
                break
            messages_in_window.insert(0, message)
            current_tokens += message.token_count

        return messages_in_window

    @property
    def message_count(self) -> int:
        """Get total number of messages."""
        return len(self.messages)

    @property
    def duration_minutes(self) -> float:
        """Get conversation duration in minutes."""
        duration = self.updated_at - self.created_at
        return duration.total_seconds() / 60

    model_config = {"json_schema_extra": {"example": {
        "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
        "user_id": "user_123",
        "status": "active",
        "created_at": "2024-11-07T10:00:00Z",
        "messages": [
            {"role": "user", "content": "What are Python best practices?"},
            {"role": "assistant", "content": "Here are some Python best practices..."},
        ],
    }}}
