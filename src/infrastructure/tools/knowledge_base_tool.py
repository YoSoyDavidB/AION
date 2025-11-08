"""
Knowledge Base tool for searching memories and documents.
"""

from typing import Any

from src.application.dtos.memory_dto import MemorySearchRequest
from src.application.use_cases.memory_use_cases import SearchMemoriesUseCase
from src.domain.entities.tool import BaseTool, ToolParameter
from src.domain.repositories.document_repository import IDocumentRepository
from src.shared.logging import LoggerMixin


class KnowledgeBaseTool(BaseTool, LoggerMixin):
    """
    Knowledge Base tool for searching through user's memories and documents.

    Allows the LLM to query the RAG system for relevant information.
    """

    def __init__(
        self,
        search_memories_use_case: SearchMemoriesUseCase,
        document_repo: IDocumentRepository,
    ):
        """
        Initialize Knowledge Base tool.

        Args:
            search_memories_use_case: Use case for searching memories
            document_repo: Repository for document operations
        """
        self.search_memories_use_case = search_memories_use_case
        self.document_repo = document_repo

    @property
    def name(self) -> str:
        return "knowledge_base_search"

    @property
    def description(self) -> str:
        return """Search through the user's knowledge base including memories and documents.
Use this tool to find relevant information that has been previously discussed or stored.
This includes:
- Past conversations and extracted facts
- User preferences and profile information
- Uploaded documents and their content
- Project information and technical details
Returns the most relevant information matching the search query."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="Search query to find relevant information in the knowledge base",
                required=True,
            ),
            ToolParameter(
                name="user_id",
                type="string",
                description="User ID to search knowledge base for",
                required=True,
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of results to return (default: 5)",
                required=False,
            ),
        ]

    async def execute(self, **kwargs: Any) -> Any:
        """
        Search knowledge base.

        Args:
            query: Search query
            user_id: User ID
            max_results: Maximum results to return (default 5)

        Returns:
            Dictionary with search results from memories and documents

        Raises:
            ValueError: If required parameters are missing
            Exception: If search fails
        """
        query = kwargs.get("query")
        user_id = kwargs.get("user_id")
        max_results = int(kwargs.get("max_results", 5))

        if not query:
            raise ValueError("Missing required parameter: query")
        if not user_id:
            raise ValueError("Missing required parameter: user_id")

        self.logger.info(
            "knowledge_base_tool_executing",
            query=query,
            user_id=user_id,
            max_results=max_results,
        )

        try:
            # Search memories
            memory_request = MemorySearchRequest(
                user_id=user_id,
                query=query,
                limit=max_results,
                min_score=0.6,  # Lower threshold for tool use
            )

            memory_results = await self.search_memories_use_case.execute(memory_request)

            # Search documents
            document_results = await self.document_repo.search_by_content(
                user_id=user_id, query=query, limit=max_results
            )

            # Format results
            results = {
                "memories": [
                    {
                        "text": mem.short_text,
                        "type": mem.memory_type.value,
                        "relevance": round(score, 3),
                        "source": mem.source,
                    }
                    for mem, score in memory_results
                ],
                "documents": [
                    {
                        "title": doc.title,
                        "content_preview": doc.content[:200] + "..."
                        if len(doc.content) > 200
                        else doc.content,
                        "tags": doc.tags,
                    }
                    for doc in document_results
                ],
                "total_results": len(memory_results) + len(document_results),
            }

            self.logger.info(
                "knowledge_base_tool_success",
                query=query,
                memories_found=len(memory_results),
                documents_found=len(document_results),
            )

            return results

        except Exception as e:
            self.logger.error(
                "knowledge_base_tool_error", query=query, error=str(e)
            )
            raise Exception(f"Knowledge base search failed: {str(e)}") from e
