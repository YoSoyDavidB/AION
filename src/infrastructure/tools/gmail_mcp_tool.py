"""
Gmail MCP tool for accessing Gmail through N8N MCP server.
"""

from typing import Any

from src.config.settings import get_settings
from src.domain.entities.tool import BaseTool, ToolParameter
from src.infrastructure.mcp import MCPN8NClient
from src.shared.logging import LoggerMixin


class GmailMCPTool(BaseTool, LoggerMixin):
    """
    Gmail tool using MCP (Model Context Protocol) via N8N.

    Communicates with N8N MCP server for all Gmail operations,
    eliminating the need for OAuth handling in AION.
    """

    def __init__(self, mcp_client: MCPN8NClient | None = None):
        """
        Initialize Gmail MCP tool.

        Args:
            mcp_client: MCP N8N client instance (optional, will create if not provided)
        """
        self.settings = get_settings()

        # Use provided client or create new one
        if mcp_client:
            self.mcp_client = mcp_client
        else:
            if not self.settings.mcp.is_gmail_configured:
                raise ValueError(
                    "Gmail MCP not configured. Set N8N_MCP_GMAIL_BASE_URL and "
                    "N8N_MCP_HEADER_VALUE environment variables."
                )

            # Remove /sse suffix if present for N8N client
            base_url = self.settings.mcp.n8n_mcp_gmail_base_url.replace("/sse", "")

            self.mcp_client = MCPN8NClient(
                base_url=base_url,
                auth_header_name=self.settings.mcp.n8n_mcp_header_name,
                auth_header_value=self.settings.mcp.n8n_mcp_header_value,
            )

        self.logger.info("gmail_mcp_tool_initialized")

    @property
    def name(self) -> str:
        return "get_email_messages"

    @property
    def description(self) -> str:
        return """Get recent email messages from Gmail.
Use this tool when the user asks about:
- Their emails or inbox
- Recent messages or correspondence
- If they received an email from someone
- Important or unread emails
- Email content or details

Returns a list of recent Gmail messages with subjects, senders, snippets, and read status."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="user_id",
                type="string",
                description="User ID to get email messages for (e.g., 'me' or email address)",
                required=True,
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of messages to return (default: 10, max: 50)",
                required=False,
            ),
            ToolParameter(
                name="only_unread",
                type="boolean",
                description="Only return unread messages (default: false)",
                required=False,
            ),
            ToolParameter(
                name="query",
                type="string",
                description="Search query to filter emails (e.g., 'from:user@example.com', 'subject:invoice')",
                required=False,
            ),
        ]

    async def execute(self, **kwargs: Any) -> Any:
        """
        Get email messages via MCP.

        Args:
            user_id: User ID (default: 'me')
            max_results: Maximum messages to return (default 10)
            only_unread: Only return unread messages (default False)
            query: Gmail search query (optional)

        Returns:
            Dictionary with email messages or error message

        Raises:
            ValueError: If required parameters are missing
            Exception: If MCP call fails
        """
        user_id = kwargs.get("user_id", "me")
        max_results = int(kwargs.get("max_results", 10))
        only_unread = kwargs.get("only_unread", False)
        query = kwargs.get("query")

        # Validate max_results
        max_results = min(max(max_results, 1), 50)

        self.logger.info(
            "gmail_mcp_getting_messages",
            user_id=user_id,
            max_results=max_results,
            only_unread=only_unread,
            has_query=bool(query),
        )

        try:
            # Prepare arguments for MCP call
            arguments = {
                "user_id": user_id,
                "max_results": max_results,
                "only_unread": only_unread,
            }

            if query:
                arguments["query"] = query

            # Connect to MCP server and call tool
            # N8N MCP uses 'search' tool for getting emails
            async with self.mcp_client as client:
                # Map parameters to N8N search tool format
                search_args = {
                    "Return_All": False,
                    "Search": "is:unread" if only_unread else "",
                    "Received_After": "",
                    "Received_Before": "",
                    "Sender": query if query else "",
                }

                result = await client.call_tool(
                    tool_name="search",
                    arguments=search_args,
                )

            # Process MCP response
            # MCP returns: {"content": [...], "isError": false}
            content = result.get("content", [])
            is_error = result.get("isError", False)

            if is_error:
                error_text = ""
                for item in content:
                    if item.get("type") == "text":
                        error_text += item.get("text", "")

                return {
                    "status": "error",
                    "error": error_text or "Unknown error from MCP server",
                    "messages": [],
                }

            # Extract messages from content
            # Parse the text content as JSON if it contains message data
            messages = []
            for item in content:
                if item.get("type") == "text":
                    text_content = item.get("text", "")
                    # Try to parse as JSON (n8n might return JSON string)
                    try:
                        import json
                        parsed = json.loads(text_content)
                        if isinstance(parsed, dict) and "messages" in parsed:
                            messages = parsed["messages"]
                        elif isinstance(parsed, list):
                            messages = parsed
                    except (json.JSONDecodeError, ValueError):
                        # If not JSON, treat as plain text response
                        pass

            self.logger.info(
                "gmail_mcp_messages_retrieved",
                user_id=user_id,
                num_messages=len(messages),
            )

            return {
                "status": "success",
                "messages": messages,
                "user_id": user_id,
            }

        except Exception as e:
            error_msg = f"Failed to get Gmail messages via MCP: {str(e)}"
            self.logger.error(
                "gmail_mcp_get_messages_error",
                user_id=user_id,
                error=str(e),
            )

            return {
                "status": "error",
                "error": error_msg,
                "messages": [],
            }

    async def send_email(
        self,
        user_id: str,
        to: str,
        subject: str,
        body: str,
        cc: str | None = None,
        bcc: str | None = None,
    ) -> dict[str, Any]:
        """
        Send an email via MCP.

        Args:
            user_id: User ID sending the email
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)

        Returns:
            Dictionary with send result
        """
        self.logger.info(
            "gmail_mcp_sending_email",
            user_id=user_id,
            to=to,
            subject=subject[:50],
        )

        try:
            arguments = {
                "user_id": user_id,
                "to": to,
                "subject": subject,
                "body": body,
            }

            if cc:
                arguments["cc"] = cc
            if bcc:
                arguments["bcc"] = bcc

            # Connect to MCP server and call tool
            async with self.mcp_client as client:
                result = await client.call_tool(
                    tool_name="send_email",
                    arguments=arguments,
                )

            self.logger.info(
                "gmail_mcp_email_sent",
                user_id=user_id,
                to=to,
            )

            return result

        except Exception as e:
            error_msg = f"Failed to send email via MCP: {str(e)}"
            self.logger.error(
                "gmail_mcp_send_email_error",
                user_id=user_id,
                to=to,
                error=str(e),
            )

            return {
                "status": "error",
                "error": error_msg,
            }

    async def health_check(self) -> bool:
        """
        Check if Gmail MCP server is healthy.

        Returns:
            True if healthy, False otherwise
        """
        return await self.mcp_client.health_check()
