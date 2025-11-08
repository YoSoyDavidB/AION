"""
SQLAlchemy database models for PostgreSQL.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from src.domain.entities.conversation import ConversationStatus, MessageRole

Base = declarative_base()


class ConversationModel(Base):
    """SQLAlchemy model for Conversation."""

    __tablename__ = "conversations"

    conversation_id = Column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id = Column(String(255), nullable=False, index=True)
    status = Column(
        Enum(ConversationStatus),
        nullable=False,
        default=ConversationStatus.ACTIVE,
        index=True,
    )
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    summary = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=False, default=dict)
    total_tokens = Column(Integer, nullable=False, default=0)

    # Relationship to messages
    messages = relationship(
        "MessageModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="MessageModel.timestamp",
    )

    # Relationship to extracted memories
    memories_extracted = relationship(
        "ConversationMemoryModel",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<ConversationModel(id={self.conversation_id}, "
            f"user={self.user_id}, status={self.status})>"
        )


class MessageModel(Base):
    """SQLAlchemy model for Message."""

    __tablename__ = "messages"

    message_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    extra_metadata = Column(JSON, nullable=False, default=dict)
    token_count = Column(Integer, nullable=False, default=0)

    # Relationship to conversation
    conversation = relationship("ConversationModel", back_populates="messages")

    def __repr__(self) -> str:
        return (
            f"<MessageModel(id={self.message_id}, "
            f"role={self.role}, conversation={self.conversation_id})>"
        )


class ConversationMemoryModel(Base):
    """
    Association table for tracking which memories were extracted from conversations.
    """

    __tablename__ = "conversation_memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to conversation
    conversation = relationship(
        "ConversationModel", back_populates="memories_extracted"
    )

    def __repr__(self) -> str:
        return (
            f"<ConversationMemoryModel(conversation={self.conversation_id}, "
            f"memory={self.memory_id})>"
        )
