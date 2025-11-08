"""
Use case for chat conversation management.
"""

from uuid import uuid4

from src.application.dtos.chat_dto import ChatRequest, ChatResponse
from src.application.dtos.entity_dto import EntityExtractionRequest
from src.application.dtos.memory_dto import MemoryCreateRequest
from src.application.dtos.rag_dto import RAGRequest
from src.application.use_cases.entity_extraction_use_case import (
    EntityExtractionUseCase,
)
from src.application.use_cases.memory_use_cases import CreateMemoryUseCase
from src.application.use_cases.rag_use_case import RAGUseCase
from src.domain.entities.conversation import Conversation, MessageRole
from src.domain.entities.memory import MemoryType, SensitivityLevel
from src.domain.repositories.conversation_repository import IConversationRepository
from src.infrastructure.llm.llm_service import LLMService
from src.shared.exceptions import UseCaseExecutionError
from src.shared.logging import LoggerMixin


class ChatUseCase(LoggerMixin):
    """
    Use case for handling chat conversations.

    This orchestrates the entire chat flow:
    1. Retrieve or create conversation
    2. Add user message
    3. Retrieve relevant context via RAG
    4. Generate assistant response
    5. Extract and store new memories
    6. Extract and store entities in knowledge graph
    7. Update conversation
    """

    def __init__(
        self,
        conversation_repo: IConversationRepository,
        rag_use_case: RAGUseCase,
        create_memory_use_case: CreateMemoryUseCase,
        entity_extraction_use_case: EntityExtractionUseCase,
        llm_service: LLMService,
    ) -> None:
        self.conversation_repo = conversation_repo
        self.rag_use_case = rag_use_case
        self.create_memory_use_case = create_memory_use_case
        self.entity_extraction_use_case = entity_extraction_use_case
        self.llm_service = llm_service

    async def execute(self, request: ChatRequest) -> ChatResponse:
        """
        Execute chat conversation (LEGACY - with blocking extractions).
        Use execute_quick() + extract_background_data() for better performance.

        Args:
            request: Chat request with user message

        Returns:
            Chat response with assistant message

        Raises:
            UseCaseExecutionError: If chat execution fails
        """
        try:
            self.logger.info(
                "executing_chat",
                user_id=request.user_id,
                message=request.message[:50],
            )

            # Step 1: Get or create conversation
            conversation = await self._get_or_create_conversation(request)

            # Step 2: Add user message
            conversation.add_message(MessageRole.USER, request.message)

            # Step 3: Generate response using RAG
            rag_request = RAGRequest(
                query=request.message,
                user_id=request.user_id,
                include_memories=request.use_memory,
                include_documents=request.use_knowledge_base,
                max_memories=request.max_context_memories,
                max_documents=request.max_context_documents,
            )

            rag_response = await self.rag_use_case.execute(rag_request)

            # Step 4: Add assistant message
            conversation.add_message(MessageRole.ASSISTANT, rag_response.answer)

            # Step 5: Extract and store new memories
            new_memories = await self._extract_memories(
                conversation_text=self._get_conversation_text(conversation),
                conversation_id=str(conversation.conversation_id),
                user_id=request.user_id,
            )

            # Step 6: Extract and store entities in knowledge graph
            entities_extracted = await self._extract_entities(
                conversation_text=self._get_conversation_text(conversation),
                conversation_id=str(conversation.conversation_id),
                user_id=request.user_id,
            )

            # Step 7: Update conversation with extracted memories
            for memory_id in new_memories:
                conversation.add_extracted_memory(memory_id)

            # Step 8: Save conversation
            await self.conversation_repo.update(conversation)

            # Step 9: Build response
            response = ChatResponse(
                conversation_id=conversation.conversation_id,
                message=rag_response.answer,
                memories_used=[
                    str(mem.memory_id) for mem in rag_response.context.memories
                ],
                documents_used=[
                    doc["doc_id"] for doc in rag_response.context.documents
                ],
                new_memories_created=[str(mem_id) for mem_id in new_memories],
                metadata={
                    "context_tokens": rag_response.context.total_tokens,
                    "confidence": rag_response.confidence,
                    "sources": rag_response.sources,
                    "entities_created": entities_extracted.get("num_entities_created", 0),
                    "relationships_created": entities_extracted.get(
                        "num_relationships_created", 0
                    ),
                },
            )

            self.logger.info(
                "chat_completed",
                conversation_id=str(conversation.conversation_id),
                new_memories=len(new_memories),
            )

            return response

        except Exception as e:
            self.logger.error("chat_execution_failed", error=str(e))
            raise UseCaseExecutionError(
                f"Chat execution failed: {str(e)}"
            ) from e

    async def execute_quick(self, request: ChatRequest) -> ChatResponse:
        """
        Execute chat conversation with quick response (extractions in background).

        Args:
            request: Chat request with user message

        Returns:
            Chat response with assistant message (extractions pending)

        Raises:
            UseCaseExecutionError: If chat execution fails
        """
        try:
            self.logger.info(
                "executing_chat_quick",
                user_id=request.user_id,
                message=request.message[:50],
            )

            # Step 1: Get or create conversation
            conversation = await self._get_or_create_conversation(request)

            # Step 2: Add user message
            conversation.add_message(MessageRole.USER, request.message)

            # Step 3: Generate response using RAG
            rag_request = RAGRequest(
                query=request.message,
                user_id=request.user_id,
                include_memories=request.use_memory,
                include_documents=request.use_knowledge_base,
                max_memories=request.max_context_memories,
                max_documents=request.max_context_documents,
            )

            rag_response = await self.rag_use_case.execute(rag_request)

            # Step 4: Add assistant message
            conversation.add_message(MessageRole.ASSISTANT, rag_response.answer)

            # Step 5: Save conversation (extractions will be done in background)
            await self.conversation_repo.update(conversation)

            # Step 6: Build quick response
            response = ChatResponse(
                conversation_id=conversation.conversation_id,
                message=rag_response.answer,
                memories_used=[
                    str(mem.memory_id) for mem in rag_response.context.memories
                ],
                documents_used=[
                    doc["doc_id"] for doc in rag_response.context.documents
                ],
                new_memories_created=[],  # Will be populated in background
                metadata={
                    "context_tokens": rag_response.context.total_tokens,
                    "confidence": rag_response.confidence,
                    "sources": rag_response.sources,
                    "entities_created": 0,  # Will be updated in background
                    "relationships_created": 0,  # Will be updated in background
                },
            )

            self.logger.info(
                "chat_quick_response_completed",
                conversation_id=str(conversation.conversation_id),
            )

            return response

        except Exception as e:
            self.logger.error("chat_quick_execution_failed", error=str(e))
            raise UseCaseExecutionError(
                f"Chat quick execution failed: {str(e)}"
            ) from e

    async def extract_background_data(
        self, conversation_id: str, user_id: str
    ) -> None:
        """
        Extract memories and entities in background after quick response.

        Args:
            conversation_id: Conversation ID
            user_id: User ID
        """
        try:
            self.logger.info(
                "extracting_background_data",
                conversation_id=conversation_id,
                user_id=user_id,
            )

            # Get conversation
            from uuid import UUID
            conversation = await self.conversation_repo.get_by_id(UUID(conversation_id))
            if not conversation:
                self.logger.warning(
                    "conversation_not_found_for_extraction",
                    conversation_id=conversation_id,
                )
                return

            conversation_text = self._get_conversation_text(conversation)

            # Extract and store new memories
            new_memories = await self._extract_memories(
                conversation_text=conversation_text,
                conversation_id=conversation_id,
                user_id=user_id,
            )

            # Extract and store entities
            await self._extract_entities(
                conversation_text=conversation_text,
                conversation_id=conversation_id,
                user_id=user_id,
            )

            # Update conversation with extracted memories
            for memory_id in new_memories:
                conversation.add_extracted_memory(memory_id)

            await self.conversation_repo.update(conversation)

            self.logger.info(
                "background_extraction_completed",
                conversation_id=conversation_id,
                new_memories=len(new_memories),
            )

        except Exception as e:
            self.logger.error(
                "background_extraction_failed",
                conversation_id=conversation_id,
                error=str(e),
            )

    async def _get_or_create_conversation(
        self, request: ChatRequest
    ) -> Conversation:
        """
        Get existing conversation or create a new one.

        Args:
            request: Chat request

        Returns:
            Conversation entity
        """
        # If conversation_id provided, try to get it
        if request.conversation_id:
            conversation = await self.conversation_repo.get_by_id(
                request.conversation_id
            )
            if conversation:
                return conversation

        # Otherwise, get active conversation or create new
        conversation = await self.conversation_repo.get_active_conversation(
            request.user_id
        )

        if conversation is None:
            # Create new conversation
            conversation = Conversation(
                user_id=request.user_id,
                messages=[],
            )
            await self.conversation_repo.create(conversation)

            self.logger.info(
                "conversation_created",
                conversation_id=str(conversation.conversation_id),
                user_id=request.user_id,
            )

        return conversation

    async def _extract_memories(
        self, conversation_text: str, conversation_id: str, user_id: str
    ) -> list:
        """
        Extract and store new memories from conversation.

        Args:
            conversation_text: Full conversation text
            conversation_id: Conversation identifier
            user_id: User identifier

        Returns:
            List of created memory IDs
        """
        try:
            # Use LLM to extract memories
            extracted = await self.llm_service.extract_memories(conversation_text)

            memory_ids = []

            for memory_data in extracted:
                # Create memory request
                memory_request = MemoryCreateRequest(
                    user_id=user_id,
                    short_text=memory_data["short_text"],
                    memory_type=MemoryType(memory_data["type"]),
                    sensitivity=SensitivityLevel(memory_data["sensitivity"]),
                    source=f"conversation_{conversation_id}",
                    relevance_score=memory_data.get("relevance_score", 1.0),
                    metadata={"extracted_from": conversation_id},
                )

                # Create memory
                memory_response = await self.create_memory_use_case.execute(
                    memory_request
                )
                memory_ids.append(memory_response.memory_id)

            self.logger.info(
                "memories_extracted",
                count=len(memory_ids),
                conversation_id=conversation_id,
            )

            return memory_ids

        except Exception as e:
            self.logger.error(
                "memory_extraction_failed",
                conversation_id=conversation_id,
                error=str(e),
            )
            # Don't fail the entire chat if memory extraction fails
            return []

    async def _extract_entities(
        self, conversation_text: str, conversation_id: str, user_id: str
    ) -> dict:
        """
        Extract and store entities from conversation.

        Args:
            conversation_text: Full conversation text
            conversation_id: Conversation identifier
            user_id: User identifier

        Returns:
            Dictionary with extraction statistics
        """
        try:
            # Extract entities using the use case
            extraction_request = EntityExtractionRequest(
                text=conversation_text,
                user_id=user_id,
                source="chat",
                metadata={"conversation_id": conversation_id},
            )

            extraction_response = await self.entity_extraction_use_case.execute(
                extraction_request
            )

            self.logger.info(
                "entities_extracted_from_conversation",
                num_entities=len(extraction_response.entities),
                num_created=extraction_response.num_entities_created,
                num_relationships=len(extraction_response.relationships),
                conversation_id=conversation_id,
            )

            return {
                "num_entities_created": extraction_response.num_entities_created,
                "num_relationships_created": extraction_response.num_relationships_created,
            }

        except Exception as e:
            self.logger.error(
                "entity_extraction_failed",
                conversation_id=conversation_id,
                error=str(e),
            )
            # Don't fail the entire chat if entity extraction fails
            return {"num_entities_created": 0, "num_relationships_created": 0}

    def _get_conversation_text(self, conversation: Conversation) -> str:
        """
        Get conversation as formatted text.

        Args:
            conversation: Conversation entity

        Returns:
            Formatted conversation text
        """
        # Get last N messages for context (avoid too long conversations)
        recent_messages = conversation.get_last_n_messages(10)

        conversation_parts = []
        for message in recent_messages:
            role = message.role.value.upper()
            conversation_parts.append(f"{role}: {message.content}")

        return "\n\n".join(conversation_parts)
