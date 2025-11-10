"""
MCP SSE Client using official Anthropic MCP SDK.
Supports Server-Sent Events (SSE) transport with authentication.
"""

from typing import Any
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client

from src.shared.logging import LoggerMixin


class MCPSseClient(LoggerMixin):
    """
    MCP client using SSE transport with the official SDK.

    Implements connection to N8N MCP Server Trigger nodes.
    """

    def __init__(
        self,
        url: str,
        auth_header_name: str = "X-API-Key",
        auth_header_value: str | None = None,
    ):
        """
        Initialize MCP SSE client.

        Args:
            url: SSE endpoint URL (e.g., https://n8n.../sse)
            auth_header_name: Name of authentication header
            auth_header_value: Value for authentication header
        """
        self.url = url
        self.auth_header_name = auth_header_name
        self.auth_header_value = auth_header_value

        # Session management
        self.session: ClientSession | None = None
        self.exit_stack: AsyncExitStack | None = None
        self._is_connected = False

        self.logger.info(
            "mcp_sse_client_initialized",
            url=url,
            has_auth=bool(auth_header_value),
        )

    def _get_headers(self) -> dict[str, str]:
        """Get authentication headers."""
        headers = {}
        if self.auth_header_value:
            headers[self.auth_header_name] = self.auth_header_value
        return headers

    async def connect(self) -> None:
        """
        Establish SSE connection to MCP server.

        Raises:
            Exception: If connection fails
        """
        if self._is_connected:
            self.logger.warning("mcp_already_connected")
            return

        try:
            self.logger.info("mcp_connecting", url=self.url)

            # Create exit stack for resource management
            self.exit_stack = AsyncExitStack()
            await self.exit_stack.__aenter__()

            # Establish SSE connection with authentication headers
            read, write = await self.exit_stack.enter_async_context(
                sse_client(
                    url=self.url,
                    headers=self._get_headers(),
                )
            )

            # Create client session
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )

            # Initialize session
            await self.session.initialize()

            self._is_connected = True

            self.logger.info("mcp_connected", url=self.url)

        except Exception as e:
            error_msg = f"Failed to connect to MCP server: {str(e)}"
            self.logger.error("mcp_connection_failed", url=self.url, error=str(e))

            # Cleanup on failure
            if self.exit_stack:
                await self.exit_stack.__aexit__(None, None, None)
                self.exit_stack = None

            raise Exception(error_msg) from e

    async def disconnect(self) -> None:
        """Close SSE connection."""
        if not self._is_connected:
            return

        try:
            self.logger.info("mcp_disconnecting")

            if self.exit_stack:
                await self.exit_stack.__aexit__(None, None, None)
                self.exit_stack = None

            self.session = None
            self._is_connected = False

            self.logger.info("mcp_disconnected")

        except Exception as e:
            self.logger.error("mcp_disconnect_error", error=str(e))

    async def list_tools(self) -> list[dict[str, Any]]:
        """
        List available tools from MCP server.

        Returns:
            List of tool definitions

        Raises:
            Exception: If not connected or request fails
        """
        if not self._is_connected or not self.session:
            raise Exception("Not connected to MCP server. Call connect() first.")

        try:
            self.logger.info("mcp_listing_tools")

            # List tools using MCP SDK
            result = await self.session.list_tools()

            # Extract tools from result
            tools = []
            if hasattr(result, 'tools'):
                for tool in result.tools:
                    tools.append({
                        "name": tool.name,
                        "description": tool.description if hasattr(tool, 'description') else "",
                        "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                    })

            self.logger.info("mcp_tools_listed", num_tools=len(tools))

            return tools

        except Exception as e:
            error_msg = f"Failed to list tools: {str(e)}"
            self.logger.error("mcp_list_tools_error", error=str(e))
            raise Exception(error_msg) from e

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Call an MCP tool.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result with content and error status

        Raises:
            Exception: If not connected or request fails
        """
        if not self._is_connected or not self.session:
            raise Exception("Not connected to MCP server. Call connect() first.")

        try:
            self.logger.info(
                "mcp_calling_tool",
                tool_name=tool_name,
                args=list(arguments.keys()),
            )

            # Call tool using MCP SDK
            result = await self.session.call_tool(
                name=tool_name,
                arguments=arguments,
            )

            # Extract content from result
            content = []
            if hasattr(result, 'content'):
                for item in result.content:
                    content_item = {
                        "type": item.type if hasattr(item, 'type') else "text",
                    }
                    if hasattr(item, 'text'):
                        content_item["text"] = item.text
                    content.append(content_item)

            is_error = getattr(result, 'isError', False)

            self.logger.info(
                "mcp_tool_called",
                tool_name=tool_name,
                is_error=is_error,
                num_content_items=len(content),
            )

            return {
                "content": content,
                "isError": is_error,
            }

        except Exception as e:
            error_msg = f"Failed to call tool '{tool_name}': {str(e)}"
            self.logger.error(
                "mcp_call_tool_error",
                tool_name=tool_name,
                error=str(e),
            )
            raise Exception(error_msg) from e

    async def health_check(self) -> bool:
        """
        Check if MCP server is healthy.

        Returns:
            True if connected and responsive, False otherwise
        """
        try:
            if not self._is_connected:
                # Try to connect
                await self.connect()

            # Try to list tools as health check
            await self.list_tools()
            return True

        except Exception as e:
            self.logger.warning("mcp_health_check_failed", error=str(e))
            return False
        finally:
            # Disconnect after health check
            if self._is_connected:
                await self.disconnect()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
