"""
Use case for RAG (Retrieval-Augmented Generation) pipeline.
"""

from src.application.dtos.memory_dto import MemoryResponse
from src.application.dtos.rag_dto import RAGContext, RAGRequest, RAGResponse
from src.domain.repositories.document_repository import IDocumentRepository
from src.domain.repositories.graph_repository import IGraphRepository
from src.domain.repositories.memory_repository import IMemoryRepository
from src.infrastructure.embeddings.embedding_service import EmbeddingService
from src.infrastructure.llm.llm_service import LLMService
from src.shared.exceptions import UseCaseExecutionError
from src.shared.logging import LoggerMixin


class RAGUseCase(LoggerMixin):
    """
    Use case for RAG-based question answering.

    This orchestrates the entire RAG pipeline:
    1. Retrieve relevant context (memories + documents + knowledge graph)
    2. Assemble context into a coherent prompt
    3. Generate answer using LLM
    """

    def __init__(
        self,
        memory_repo: IMemoryRepository,
        document_repo: IDocumentRepository,
        embedding_service: EmbeddingService,
        llm_service: LLMService,
        graph_repo: IGraphRepository | None = None,
    ) -> None:
        self.memory_repo = memory_repo
        self.document_repo = document_repo
        self.embedding_service = embedding_service
        self.llm_service = llm_service
        self.graph_repo = graph_repo

    async def execute(self, request: RAGRequest) -> RAGResponse:
        """
        Execute RAG pipeline.

        Args:
            request: RAG request with query and parameters

        Returns:
            RAG response with answer and context

        Raises:
            UseCaseExecutionError: If RAG execution fails
        """
        try:
            self.logger.info(
                "executing_rag_pipeline",
                query=request.query[:50],
                user_id=request.user_id,
            )

            # Step 1: Retrieve context
            context = await self._retrieve_context(request)

            # Step 2: Generate answer
            answer = await self._generate_answer(request, context)

            # Step 3: Extract sources
            sources = self._extract_sources(context)

            response = RAGResponse(
                answer=answer,
                context=context,
                confidence=0.85,  # TODO: Implement confidence scoring
                sources=sources,
            )

            self.logger.info(
                "rag_pipeline_completed",
                answer_length=len(answer),
                num_sources=len(sources),
            )

            return response

        except Exception as e:
            self.logger.error("rag_pipeline_failed", error=str(e))
            raise UseCaseExecutionError(
                f"RAG pipeline failed: {str(e)}"
            ) from e

    async def _retrieve_context(self, request: RAGRequest) -> RAGContext:
        """
        Retrieve relevant context from memories and documents.

        Args:
            request: RAG request

        Returns:
            Assembled context
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_query(request.query)

        memories = []
        documents = []

        # Retrieve memories if requested
        if request.include_memories and request.max_memories > 0:
            memory_results = await self.memory_repo.search_similar(
                query_embedding=query_embedding,
                user_id=request.user_id,
                limit=request.max_memories,
                min_score=0.3,  # Lowered threshold for better recall
            )

            memories = [
                MemoryResponse(
                    memory_id=mem.memory_id,
                    short_text=mem.short_text,
                    memory_type=mem.memory_type,
                    sensitivity=mem.sensitivity,
                    relevance_score=mem.relevance_score,
                    num_times_referenced=mem.num_times_referenced,
                    source=mem.source,
                    created_at=mem.timestamp.isoformat(),
                    last_referenced_at=mem.last_referenced_at.isoformat(),
                )
                for mem, score in memory_results
            ]

        # Retrieve documents if requested
        if request.include_documents and request.max_documents > 0:
            doc_results = await self.document_repo.search_similar(
                query_embedding=query_embedding,
                user_id=request.user_id,
                limit=request.max_documents,
                min_score=0.3,  # Lowered threshold for better recall
            )

            documents = [
                {
                    "doc_id": str(doc.doc_id),
                    "title": doc.title,
                    "content": doc.content,
                    "path": doc.path,
                    "heading": doc.heading,
                    "tags": doc.tags,
                    "score": score,
                }
                for doc, score in doc_results
            ]

        # Retrieve entities from knowledge graph if available
        entities = []
        if self.graph_repo:
            entities = await self._retrieve_entities(request.query)

        # Assemble context text
        context_text = self._assemble_context_text(memories, documents, entities)

        # Estimate token count (rough approximation)
        total_tokens = len(context_text) // 4

        return RAGContext(
            memories=memories,
            documents=documents,
            context_text=context_text,
            total_tokens=total_tokens,
        )

    async def _retrieve_entities(self, query: str) -> list[dict]:
        """
        Retrieve relevant entities from knowledge graph.

        Args:
            query: User query

        Returns:
            List of entity dictionaries with relationships
        """
        try:
            # Search for entities matching the query
            search_results = await self.graph_repo.search_entities(
                query=query,
                entity_type=None,  # Search all types
                limit=5,  # Limit to top 5 entities
            )

            entities_with_relations = []

            for result in search_results:
                entity = result.entity

                # Get relationships for this entity
                relationships = await self.graph_repo.get_entity_relationships(
                    entity_id=entity.entity_id,
                    direction="both",
                )

                # Get related entities
                related_entities = []
                for rel in relationships[:3]:  # Limit to 3 relationships per entity
                    # Get the target entity
                    if rel.source_entity_id == entity.entity_id:
                        related = await self.graph_repo.get_entity_by_id(
                            rel.target_entity_id
                        )
                        direction = "outgoing"
                    else:
                        related = await self.graph_repo.get_entity_by_id(
                            rel.source_entity_id
                        )
                        direction = "incoming"

                    if related:
                        related_entities.append({
                            "name": related.name,
                            "type": related.entity_type.value,
                            "relationship": rel.relationship_type.value,
                            "direction": direction,
                        })

                entities_with_relations.append({
                    "name": entity.name,
                    "type": entity.entity_type.value,
                    "description": entity.description,
                    "properties": entity.properties,
                    "related": related_entities,
                })

            self.logger.info(
                "entities_retrieved_for_rag",
                count=len(entities_with_relations),
            )

            return entities_with_relations

        except Exception as e:
            self.logger.error(
                "entity_retrieval_failed",
                query=query,
                error=str(e),
            )
            # Don't fail the entire RAG pipeline if entity retrieval fails
            return []

    def _assemble_context_text(
        self, memories: list[MemoryResponse], documents: list[dict], entities: list[dict]
    ) -> str:
        """
        Assemble context from memories, documents, and entities into text.

        Args:
            memories: Retrieved memories
            documents: Retrieved documents
            entities: Retrieved entities from knowledge graph

        Returns:
            Assembled context text
        """
        context_parts = []

        # Add memories
        if memories:
            memory_text = "## Relevant Memories\n\n"
            for i, memory in enumerate(memories, 1):
                memory_text += f"{i}. [{memory.memory_type.value}] {memory.short_text}\n"
            context_parts.append(memory_text)

        # Add documents
        if documents:
            doc_text = "## Relevant Knowledge Base Documents\n\n"
            for i, doc in enumerate(documents, 1):
                heading = f" - {doc['heading']}" if doc.get("heading") else ""
                doc_text += f"{i}. **{doc['title']}{heading}**\n"
                doc_text += f"   Path: {doc['path']}\n"
                doc_text += f"   Content: {doc['content'][:300]}...\n\n"
            context_parts.append(doc_text)

        # Add entities from knowledge graph
        if entities:
            entity_text = "## Knowledge Graph Entities\n\n"
            for i, entity in enumerate(entities, 1):
                entity_text += f"{i}. **{entity['name']}** ({entity['type']})\n"
                if entity.get("description"):
                    entity_text += f"   {entity['description']}\n"

                # Add related entities
                if entity.get("related"):
                    entity_text += f"   Relationships:\n"
                    for rel in entity["related"]:
                        rel_symbol = "->" if rel["direction"] == "outgoing" else "<-"
                        entity_text += f"   - {rel_symbol} {rel['relationship']}: {rel['name']} ({rel['type']})\n"

                entity_text += "\n"
            context_parts.append(entity_text)

        return "\n".join(context_parts) if context_parts else "No relevant context found."

    async def _generate_answer(
        self, request: RAGRequest, context: RAGContext
    ) -> str:
        """
        Generate answer using LLM with retrieved context.

        Args:
            request: RAG request
            context: Retrieved context

        Returns:
            Generated answer
        """
        answer = await self.llm_service.answer_with_context(
            question=request.query,
            context=context.context_text,
            system_prompt=request.system_prompt,
        )

        return answer

    def _extract_sources(self, context: RAGContext) -> list[str]:
        """
        Extract source citations from context.

        Args:
            context: RAG context

        Returns:
            List of source citations
        """
        sources = []

        # Add memory sources
        for memory in context.memories:
            sources.append(f"Memory: {memory.source}")

        # Add document sources
        for doc in context.documents:
            sources.append(f"Document: {doc['path']}")

        return list(set(sources))  # Remove duplicates
