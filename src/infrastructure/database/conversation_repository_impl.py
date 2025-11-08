"""
PostgreSQL implementation of Conversation repository.
"""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.entities.conversation import Conversation, ConversationStatus, Message
from src.domain.repositories.conversation_repository import IConversationRepository
from src.infrastructure.database.connection import get_db_manager
from src.infrastructure.database.models import (
    ConversationMemoryModel,
    ConversationModel,
    MessageModel,
)
from src.shared.exceptions import DatabaseError, EntityNotFoundError
from src.shared.logging import LoggerMixin


class PostgreSQLConversationRepository(IConversationRepository, LoggerMixin):
    """
    PostgreSQL implementation of Conversation repository.

    Stores conversations and messages in a relational database.
    """

    def __init__(self) -> None:
        """Initialize repository."""
        self.db_manager = get_db_manager()
        self.logger.info("conversation_repository_initialized")

    async def initialize(self) -> None:
        """Initialize database tables."""
        await self.db_manager.create_tables()

    def _model_to_entity(self, model: ConversationModel) -> Conversation:
        """Convert database model to domain entity."""
        messages = [
            Message(
                message_id=msg.message_id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                metadata=msg.extra_metadata,
                token_count=msg.token_count,
            )
            for msg in model.messages
        ]

        memories_extracted = [
            mem.memory_id for mem in model.memories_extracted
        ]

        return Conversation(
            conversation_id=model.conversation_id,
            user_id=model.user_id,
            messages=messages,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at,
            memories_extracted=memories_extracted,
            summary=model.summary,
            metadata=model.extra_metadata,
            total_tokens=model.total_tokens,
        )

    def _entity_to_model(
        self, conversation: Conversation, model: ConversationModel | None = None
    ) -> ConversationModel:
        """Convert domain entity to database model."""
        if model is None:
            model = ConversationModel()

        model.conversation_id = conversation.conversation_id
        model.user_id = conversation.user_id
        model.status = conversation.status
        model.created_at = conversation.created_at
        model.updated_at = conversation.updated_at
        model.summary = conversation.summary
        model.extra_metadata = conversation.metadata
        model.total_tokens = conversation.total_tokens

        return model

    async def create(self, conversation: Conversation) -> Conversation:
        """Create a new conversation."""
        try:
            async with self.db_manager.get_session() as session:
                model = self._entity_to_model(conversation)

                # Add messages
                for message in conversation.messages:
                    msg_model = MessageModel(
                        message_id=message.message_id,
                        conversation_id=conversation.conversation_id,
                        role=message.role,
                        content=message.content,
                        timestamp=message.timestamp,
                        extra_metadata=message.metadata,
                        token_count=message.token_count,
                    )
                    model.messages.append(msg_model)

                session.add(model)
                await session.flush()

                self.logger.info(
                    "conversation_created",
                    conversation_id=str(conversation.conversation_id),
                )

                return conversation

        except Exception as e:
            self.logger.error(
                "conversation_creation_failed",
                conversation_id=str(conversation.conversation_id),
                error=str(e),
            )
            raise DatabaseError(
                f"Failed to create conversation: {str(e)}"
            ) from e

    async def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        """Retrieve a conversation by ID."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = (
                    select(ConversationModel)
                    .where(ConversationModel.conversation_id == conversation_id)
                    .options(
                        selectinload(ConversationModel.messages),
                        selectinload(ConversationModel.memories_extracted),
                    )
                )

                result = await session.execute(stmt)
                model = result.scalar_one_or_none()

                if model is None:
                    return None

                return self._model_to_entity(model)

        except Exception as e:
            self.logger.error(
                "conversation_retrieval_failed",
                conversation_id=str(conversation_id),
                error=str(e),
            )
            raise DatabaseError(
                f"Failed to retrieve conversation: {str(e)}"
            ) from e

    async def update(self, conversation: Conversation) -> Conversation:
        """Update an existing conversation."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = (
                    select(ConversationModel)
                    .where(
                        ConversationModel.conversation_id == conversation.conversation_id
                    )
                    .options(
                        selectinload(ConversationModel.messages),
                        selectinload(ConversationModel.memories_extracted),
                    )
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()

                if model is None:
                    raise EntityNotFoundError(
                        "Conversation", str(conversation.conversation_id)
                    )

                # Update conversation fields
                self._entity_to_model(conversation, model)

                # Clear existing messages and add new ones
                model.messages.clear()
                for message in conversation.messages:
                    msg_model = MessageModel(
                        message_id=message.message_id,
                        conversation_id=conversation.conversation_id,
                        role=message.role,
                        content=message.content,
                        timestamp=message.timestamp,
                        extra_metadata=message.metadata,
                        token_count=message.token_count,
                    )
                    model.messages.append(msg_model)

                await session.flush()

                self.logger.info(
                    "conversation_updated",
                    conversation_id=str(conversation.conversation_id),
                )

                return conversation

        except EntityNotFoundError:
            raise
        except Exception as e:
            self.logger.error(
                "conversation_update_failed",
                conversation_id=str(conversation.conversation_id),
                error=str(e),
            )
            raise DatabaseError(
                f"Failed to update conversation: {str(e)}"
            ) from e

    async def delete(self, conversation_id: UUID) -> bool:
        """Delete a conversation."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(ConversationModel).where(
                    ConversationModel.conversation_id == conversation_id
                )
                result = await session.execute(stmt)
                model = result.scalar_one_or_none()

                if model is None:
                    return False

                await session.delete(model)
                await session.flush()

                self.logger.info(
                    "conversation_deleted",
                    conversation_id=str(conversation_id),
                )

                return True

        except Exception as e:
            self.logger.error(
                "conversation_deletion_failed",
                conversation_id=str(conversation_id),
                error=str(e),
            )
            raise DatabaseError(
                f"Failed to delete conversation: {str(e)}"
            ) from e

    async def get_by_user(
        self,
        user_id: str,
        status: ConversationStatus | None = None,
        limit: int = 100,
    ) -> list[Conversation]:
        """Get conversations for a specific user."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = (
                    select(ConversationModel)
                    .where(ConversationModel.user_id == user_id)
                    .options(
                        selectinload(ConversationModel.messages),
                        selectinload(ConversationModel.memories_extracted),
                    )
                    .order_by(ConversationModel.updated_at.desc())
                    .limit(limit)
                )

                if status:
                    stmt = stmt.where(ConversationModel.status == status)

                result = await session.execute(stmt)
                models = result.scalars().all()

                conversations = [self._model_to_entity(model) for model in models]

                return conversations

        except Exception as e:
            self.logger.error(
                "get_by_user_failed",
                user_id=user_id,
                error=str(e),
            )
            raise DatabaseError(
                f"Failed to get conversations by user: {str(e)}"
            ) from e

    async def get_active_conversation(
        self, user_id: str
    ) -> Conversation | None:
        """Get the active conversation for a user."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = (
                    select(ConversationModel)
                    .where(
                        and_(
                            ConversationModel.user_id == user_id,
                            ConversationModel.status == ConversationStatus.ACTIVE,
                        )
                    )
                    .options(
                        selectinload(ConversationModel.messages),
                        selectinload(ConversationModel.memories_extracted),
                    )
                    .order_by(ConversationModel.updated_at.desc())
                    .limit(1)
                )

                result = await session.execute(stmt)
                model = result.scalar_one_or_none()

                if model is None:
                    return None

                return self._model_to_entity(model)

        except Exception as e:
            self.logger.error(
                "get_active_conversation_failed",
                user_id=user_id,
                error=str(e),
            )
            raise DatabaseError(
                f"Failed to get active conversation: {str(e)}"
            ) from e

    async def get_recent(
        self,
        user_id: str | None = None,
        days: int = 7,
        limit: int = 10,
    ) -> list[Conversation]:
        """Get recent conversations."""
        try:
            async with self.db_manager.get_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days)

                stmt = (
                    select(ConversationModel)
                    .where(ConversationModel.updated_at >= cutoff_date)
                    .options(
                        selectinload(ConversationModel.messages),
                        selectinload(ConversationModel.memories_extracted),
                    )
                    .order_by(ConversationModel.updated_at.desc())
                    .limit(limit)
                )

                if user_id:
                    stmt = stmt.where(ConversationModel.user_id == user_id)

                result = await session.execute(stmt)
                models = result.scalars().all()

                conversations = [self._model_to_entity(model) for model in models]

                return conversations

        except Exception as e:
            self.logger.error("get_recent_failed", error=str(e))
            raise DatabaseError(
                f"Failed to get recent conversations: {str(e)}"
            ) from e

    async def search_by_content(
        self, query: str, user_id: str | None = None, limit: int = 10
    ) -> list[Conversation]:
        """Search conversations by message content."""
        try:
            async with self.db_manager.get_session() as session:
                # Search in message content
                subquery = (
                    select(MessageModel.conversation_id)
                    .where(MessageModel.content.ilike(f"%{query}%"))
                    .distinct()
                )

                stmt = (
                    select(ConversationModel)
                    .where(ConversationModel.conversation_id.in_(subquery))
                    .options(
                        selectinload(ConversationModel.messages),
                        selectinload(ConversationModel.memories_extracted),
                    )
                    .limit(limit)
                )

                if user_id:
                    stmt = stmt.where(ConversationModel.user_id == user_id)

                result = await session.execute(stmt)
                models = result.scalars().all()

                conversations = [self._model_to_entity(model) for model in models]

                return conversations

        except Exception as e:
            self.logger.error("search_by_content_failed", error=str(e))
            raise DatabaseError(
                f"Failed to search conversations: {str(e)}"
            ) from e

    async def count(
        self,
        user_id: str | None = None,
        status: ConversationStatus | None = None,
    ) -> int:
        """Count conversations, optionally filtered."""
        try:
            async with self.db_manager.get_session() as session:
                stmt = select(func.count(ConversationModel.conversation_id))

                conditions = []
                if user_id:
                    conditions.append(ConversationModel.user_id == user_id)
                if status:
                    conditions.append(ConversationModel.status == status)

                if conditions:
                    stmt = stmt.where(and_(*conditions))

                result = await session.execute(stmt)
                count = result.scalar_one()

                return count

        except Exception as e:
            self.logger.error("count_failed", error=str(e))
            raise DatabaseError(
                f"Failed to count conversations: {str(e)}"
            ) from e

    async def archive_old_conversations(
        self, days_threshold: int = 30
    ) -> int:
        """Archive conversations older than threshold."""
        try:
            async with self.db_manager.get_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

                stmt = (
                    select(ConversationModel)
                    .where(
                        and_(
                            ConversationModel.updated_at < cutoff_date,
                            ConversationModel.status != ConversationStatus.ARCHIVED,
                        )
                    )
                )

                result = await session.execute(stmt)
                models = result.scalars().all()

                count = 0
                for model in models:
                    model.status = ConversationStatus.ARCHIVED
                    model.updated_at = datetime.utcnow()
                    count += 1

                await session.flush()

                self.logger.info("conversations_archived", count=count)

                return count

        except Exception as e:
            self.logger.error("archive_old_failed", error=str(e))
            raise DatabaseError(
                f"Failed to archive old conversations: {str(e)}"
            ) from e

    async def get_conversation_stats(
        self, user_id: str
    ) -> dict[str, int]:
        """Get conversation statistics for a user."""
        try:
            async with self.db_manager.get_session() as session:
                total_stmt = select(
                    func.count(ConversationModel.conversation_id)
                ).where(ConversationModel.user_id == user_id)

                active_stmt = select(
                    func.count(ConversationModel.conversation_id)
                ).where(
                    and_(
                        ConversationModel.user_id == user_id,
                        ConversationModel.status == ConversationStatus.ACTIVE,
                    )
                )

                completed_stmt = select(
                    func.count(ConversationModel.conversation_id)
                ).where(
                    and_(
                        ConversationModel.user_id == user_id,
                        ConversationModel.status == ConversationStatus.COMPLETED,
                    )
                )

                archived_stmt = select(
                    func.count(ConversationModel.conversation_id)
                ).where(
                    and_(
                        ConversationModel.user_id == user_id,
                        ConversationModel.status == ConversationStatus.ARCHIVED,
                    )
                )

                total = (await session.execute(total_stmt)).scalar_one()
                active = (await session.execute(active_stmt)).scalar_one()
                completed = (await session.execute(completed_stmt)).scalar_one()
                archived = (await session.execute(archived_stmt)).scalar_one()

                return {
                    "total": total,
                    "active": active,
                    "completed": completed,
                    "archived": archived,
                }

        except Exception as e:
            self.logger.error(
                "get_conversation_stats_failed",
                user_id=user_id,
                error=str(e),
            )
            raise DatabaseError(
                f"Failed to get conversation stats: {str(e)}"
            ) from e
