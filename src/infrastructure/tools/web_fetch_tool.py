"""
Web Fetch tool for retrieving and parsing web page content.
"""

from typing import Any

import httpx
from bs4 import BeautifulSoup

from src.domain.entities.tool import BaseTool, ToolParameter
from src.shared.logging import LoggerMixin


class WebFetchTool(BaseTool, LoggerMixin):
    """
    Web Fetch tool for retrieving and parsing web page content.

    Downloads a web page and extracts its text content for analysis.
    """

    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return """Fetch and read the FULL CONTENT of a web page. This is ESSENTIAL after web_search.

IMPORTANT: web_search only returns SHORT SNIPPETS. To get actual information, you MUST use web_fetch.

Use this tool when you need to:
- Read complete content from URLs found via web_search (REQUIRED for weather, news, articles)
- Extract detailed information that snippets don't contain
- Get the actual data from weather sites, news articles, or any web page

Example workflow:
1. Use web_search to find relevant URLs
2. Use web_fetch on 1-2 of the most relevant URLs
3. Analyze the full content to answer the user's question

Returns the main text content of the web page, cleaned and formatted."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="url",
                type="string",
                description="The URL of the web page to fetch and read",
                required=True,
            ),
        ]

    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute web page fetching and content extraction.

        Args:
            url: URL of the page to fetch

        Returns:
            Dictionary with URL, title, and extracted text content

        Raises:
            ValueError: If URL is missing or invalid
            Exception: If fetching or parsing fails
        """
        url = kwargs.get("url")

        if not url:
            raise ValueError("Missing required parameter: url")

        # Basic URL validation
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        self.logger.info("web_fetch_tool_executing", url=url)

        try:
            # Fetch the web page
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; AION/1.0; +https://github.com/yourusername/aion)"
                },
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

            # Parse HTML content
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get title
            title = soup.title.string if soup.title else "No title"

            # Extract main content - try common content containers first
            main_content = None
            for selector in ["main", "article", '[role="main"]', ".content", "#content"]:
                main_content = soup.select_one(selector)
                if main_content:
                    break

            # If no main content found, use body
            if not main_content:
                main_content = soup.body

            # Extract text
            if main_content:
                text = main_content.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)

            # Clean up text: remove excessive whitespace
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            cleaned_text = "\n".join(lines)

            # Limit content length to avoid token overload
            max_chars = 8000
            if len(cleaned_text) > max_chars:
                cleaned_text = cleaned_text[:max_chars] + "\n\n[Content truncated...]"

            self.logger.info(
                "web_fetch_tool_success",
                url=url,
                title=title,
                content_length=len(cleaned_text),
            )

            return {
                "url": url,
                "title": title,
                "content": cleaned_text,
                "status": "success",
            }

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error {e.response.status_code}: {e.response.reason_phrase}"
            self.logger.error("web_fetch_tool_http_error", url=url, error=error_msg)
            return {
                "url": url,
                "error": error_msg,
                "status": "error",
            }

        except httpx.TimeoutException:
            error_msg = "Request timed out after 30 seconds"
            self.logger.error("web_fetch_tool_timeout", url=url)
            return {
                "url": url,
                "error": error_msg,
                "status": "error",
            }

        except Exception as e:
            error_msg = f"Failed to fetch page: {str(e)}"
            self.logger.error("web_fetch_tool_error", url=url, error=str(e))
            return {
                "url": url,
                "error": error_msg,
                "status": "error",
            }
