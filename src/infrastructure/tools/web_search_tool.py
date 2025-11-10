"""
Web Search tool for searching the internet.
"""

from typing import Any

from src.domain.entities.tool import BaseTool, ToolParameter
from src.shared.logging import LoggerMixin


class WebSearchTool(BaseTool, LoggerMixin):
    """
    Web Search tool for searching the internet using DuckDuckGo.

    Provides access to up-to-date information from the web.
    """

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return """Search the internet for current information, news, facts, and answers.
Use this tool when you need:
- Current/recent information not in the knowledge base
- Real-time data (weather, news, stock prices, etc.)
- General web information or facts
- To verify or supplement existing knowledge

IMPORTANT: This tool returns ONLY snippets and URLs. For complete information:
1. Use web_search to find relevant URLs
2. Then use web_fetch to read the FULL CONTENT of promising pages
3. Snippets alone are usually insufficient for detailed answers

Returns top search results with titles, SHORT SNIPPETS, and URLs."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="string",
                description="Search query to find information on the web",
                required=True,
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of results to return (default: 5, max: 10)",
                required=False,
            ),
        ]

    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute web search.

        Args:
            query: Search query
            max_results: Maximum results to return (default 5)

        Returns:
            List of search results with title, snippet, and URL

        Raises:
            ValueError: If query is missing
            Exception: If search fails
        """
        query = kwargs.get("query")
        max_results = int(kwargs.get("max_results", 5))

        if not query:
            raise ValueError("Missing required parameter: query")

        # Limit max results
        max_results = min(max_results, 10)

        self.logger.info(
            "web_search_tool_executing",
            query=query,
            max_results=max_results,
        )

        try:
            from duckduckgo_search import DDGS

            # Perform search
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(
                    {
                        "position": i,
                        "title": result.get("title", ""),
                        "snippet": result.get("body", ""),
                        "url": result.get("href", ""),
                    }
                )

            self.logger.info(
                "web_search_tool_success",
                query=query,
                results_found=len(formatted_results),
            )

            return {
                "query": query,
                "results_count": len(formatted_results),
                "results": formatted_results,
            }

        except Exception as e:
            self.logger.error(
                "web_search_tool_error", query=query, error=str(e)
            )
            raise Exception(f"Web search failed: {str(e)}") from e
