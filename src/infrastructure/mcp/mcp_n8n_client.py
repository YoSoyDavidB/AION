"""
MCP Client for N8N MCP Server Trigger.
Implements the N8N-specific HTTP protocol with sessions.
"""

import asyncio
import uuid
from typing import Any

import httpx

from src.shared.logging import LoggerMixin


class MCPN8NClient(LoggerMixin):
    """
    MCP client for N8N MCP Server Trigger nodes.

    Follows the N8N-specific protocol:
    1. GET /sse to get endpoint with sessionId
    2. POST /messages?sessionId=X with 'initialize'
    3. Extract Mcp-Session-Id header
    4. POST /messages with tools/call using Mcp-Session-Id
    """

    def __init__(
        self,
        base_url: str,
        auth_header_name: str = "X-API-Key",
        auth_header_value: str | None = None,
        timeout: int = 30,
    ):
        """
        Initialize N8N MCP client.

        Args:
            base_url: Base URL of the MCP server (e.g., https://n8n.../mcp/gmail)
            auth_header_name: Name of authentication header
            auth_header_value: Value for authentication header
            timeout: Request timeout in seconds
        """
        # Remove /sse suffix if present
        self.base_url = base_url.rstrip("/").replace("/sse", "")
        self.auth_header_name = auth_header_name
        self.auth_header_value = auth_header_value
        self.timeout = timeout

        # Session management
        self.session_id: str | None = None
        self.mcp_session_id: str | None = None
        self._request_id = 0

        self.logger.info(
            "mcp_n8n_client_initialized",
            base_url=self.base_url,
            has_auth=bool(auth_header_value),
        )

    def _get_next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    def _get_headers(self, include_mcp_session: bool = False) -> dict[str, str]:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",  # N8N requires both
        }

        # Add authentication
        if self.auth_header_value:
            headers[self.auth_header_name] = self.auth_header_value

        # Add MCP session ID if initialized
        if include_mcp_session and self.mcp_session_id:
            headers["Mcp-Session-Id"] = self.mcp_session_id

        return headers

    async def initialize_session(self) -> None:
        """
        Initialize MCP session.

        Steps:
        1. GET /sse to get sessionId
        2. POST /messages?sessionId=X with initialize
        3. Extract Mcp-Session-Id from response headers
        """
        try:
            # Step 1: Get session ID from endpoint
            self.logger.info("mcp_getting_session_id", url=f"{self.base_url}/sse")

            # Use curl to fetch SSE endpoint (Python HTTP clients have issues with this endpoint)
            cmd = [
                "curl",
                "-N",  # Disable buffering
                "-H", f"{self.auth_header_name}: {self.auth_header_value}",
                f"{self.base_url}/sse",
                "--max-time", "3",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()
            sse_data = stdout.decode("utf-8")

            # Extract sessionId from SSE data
            # Format: "event: endpoint\ndata: /mcp/gmail/messages?sessionId=xxx\n\n"
            if "sessionId=" in sse_data:
                session_id_part = sse_data.split("sessionId=")[1]
                self.session_id = session_id_part.split()[0].strip()
            else:
                # Generate our own session ID
                self.session_id = f"session-{uuid.uuid4()}"

            self.logger.info("mcp_session_id_obtained", session_id=self.session_id)

            # Step 2: Initialize the session
            self.logger.info("mcp_initializing_session")

            messages_url = f"{self.base_url}/messages?sessionId={self.session_id}"

            init_request = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "aion-mcp-client",
                        "version": "1.0.0",
                    },
                },
            }

            # Create new HTTP client for this request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    messages_url,
                    json=init_request,
                    headers=self._get_headers(include_mcp_session=False),
                )

            # Log initialize response
            self.logger.info(
                "mcp_initialize_response",
                status=response.status_code,
                headers=dict(response.headers),
                body=response.text[:500],
            )

            response.raise_for_status()

            # Parse SSE response
            # Format: "event: message\ndata: {...}\n\n"
            import json

            response_text = response.text
            if "data: " in response_text:
                # Extract JSON from SSE data field
                data_line = [line for line in response_text.split("\n") if line.startswith("data: ")][0]
                json_str = data_line.replace("data: ", "")
                init_result = json.loads(json_str)

                # Check for errors in result
                if "error" in init_result:
                    raise Exception(f"Initialize failed: {init_result['error']}")

                self.logger.info(
                    "mcp_initialize_success",
                    result=init_result.get("result", {}),
                )

                # Step 3: Extract Mcp-Session-Id from response headers
                self.mcp_session_id = response.headers.get("Mcp-Session-Id")

                if not self.mcp_session_id:
                    # Some servers return it lowercase
                    self.mcp_session_id = response.headers.get("mcp-session-id")

                if not self.mcp_session_id:
                    raise Exception("Server did not return Mcp-Session-Id header")

                self.logger.info(
                    "mcp_session_initialized",
                    mcp_session_id=self.mcp_session_id[:20] + "...",
                )

        except Exception as e:
            error_msg = f"Failed to initialize MCP session: {str(e)}"
            self.logger.error("mcp_session_init_failed", error=str(e))
            raise Exception(error_msg) from e

    async def list_tools(self) -> list[dict[str, Any]]:
        """
        List available tools from MCP server.

        Returns:
            List of tool definitions

        Raises:
            Exception: If not initialized or request fails
        """
        if not self.mcp_session_id:
            await self.initialize_session()

        try:
            self.logger.info("mcp_listing_tools")

            # After initialization, use ONLY Mcp-Session-Id header, not sessionId URL param
            messages_url = f"{self.base_url}/messages"

            list_request = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "tools/list",
                "params": {},
            }

            headers = self._get_headers(include_mcp_session=True)

            # Log exact request details
            self.logger.info(
                "mcp_list_tools_request",
                url=messages_url,
                headers=headers,
                body=list_request,
            )

            # Create new HTTP client for this request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    messages_url,
                    json=list_request,
                    headers=headers,
                )

            # Log response for debugging
            self.logger.info(
                "mcp_list_tools_response",
                status=response.status_code,
                body=response.text[:500],
            )

            response.raise_for_status()

            # Parse SSE response format
            # Format: "event: message\ndata: {...}\n\n"
            import json

            response_text = response.text
            if "data: " in response_text:
                # Extract JSON from SSE data field
                data_line = [line for line in response_text.split("\n") if line.startswith("data: ")][0]
                json_str = data_line.replace("data: ", "")
                result = json.loads(json_str)
            else:
                # Fallback to plain JSON if not SSE format
                result = response.json()

            # Extract tools from result
            tools = result.get("result", {}).get("tools", [])

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
            Tool execution result with content

        Raises:
            Exception: If not initialized or request fails
        """
        if not self.mcp_session_id:
            await self.initialize_session()

        try:
            self.logger.info(
                "mcp_calling_tool",
                tool_name=tool_name,
                args=list(arguments.keys()),
            )

            # After initialization, use ONLY Mcp-Session-Id header, not sessionId URL param
            messages_url = f"{self.base_url}/messages"

            call_request = {
                "jsonrpc": "2.0",
                "id": self._get_next_id(),
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments,
                },
            }

            # Create new HTTP client for this request
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    messages_url,
                    json=call_request,
                    headers=self._get_headers(include_mcp_session=True),
                )

            response.raise_for_status()

            # Parse SSE response format
            # Format: "event: message\ndata: {...}\n\n"
            import json

            response_text = response.text
            if "data: " in response_text:
                # Extract JSON from SSE data field
                data_line = [line for line in response_text.split("\n") if line.startswith("data: ")][0]
                json_str = data_line.replace("data: ", "")
                result = json.loads(json_str)
            else:
                # Fallback to plain JSON if not SSE format
                result = response.json()

            # Extract content from result
            tool_result = result.get("result", {})
            content = tool_result.get("content", [])
            is_error = tool_result.get("isError", False)

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
            True if can connect and initialize, False otherwise
        """
        try:
            await self.initialize_session()
            return True
        except Exception as e:
            self.logger.warning("mcp_health_check_failed", error=str(e))
            return False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Clean up session
        self.session_id = None
        self.mcp_session_id = None
