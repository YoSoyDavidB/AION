"""
MCP (Model Context Protocol) client using JSON-RPC 2.0.
Implements the official MCP specification for communication with MCP servers.
"""

import uuid
from typing import Any

import httpx

from src.shared.logging import LoggerMixin


class MCPJsonRpcClient(LoggerMixin):
    """
    MCP client implementing JSON-RPC 2.0 protocol.

    Follows the official Model Context Protocol specification:
    https://modelcontextprotocol.io/specification
    """

    def __init__(
        self,
        base_url: str,
        auth_header_name: str = "X-API-Key",
        auth_header_value: str | None = None,
        timeout: int = 30,
    ):
        """
        Initialize MCP JSON-RPC client.

        Args:
            base_url: Base URL of the MCP server (e.g., https://n8n.../sse)
            auth_header_name: Name of authentication header
            auth_header_value: Value for authentication header
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.auth_header_name = auth_header_name
        self.auth_header_value = auth_header_value
        self.timeout = timeout
        self._request_id = 0

        self.logger.info(
            "mcp_jsonrpc_client_initialized",
            base_url=base_url,
            has_auth=bool(auth_header_value),
        )

    def _get_next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    def _get_headers(self, additional_headers: dict[str, str] | None = None) -> dict[str, str]:
        """
        Get request headers with authentication.

        Args:
            additional_headers: Additional headers to include

        Returns:
            Complete headers dictionary
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Add authentication header if configured
        if self.auth_header_value:
            headers[self.auth_header_name] = self.auth_header_value

        # Add any additional headers
        if additional_headers:
            headers.update(additional_headers)

        return headers

    async def _send_jsonrpc_request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send a JSON-RPC 2.0 request to the MCP server.

        Args:
            method: JSON-RPC method name (e.g., "tools/list", "tools/call")
            params: Method parameters

        Returns:
            JSON-RPC result

        Raises:
            Exception: If the request fails
        """
        request_id = self._get_next_id()

        # Build JSON-RPC 2.0 request
        jsonrpc_request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }

        if params:
            jsonrpc_request["params"] = params

        self.logger.info(
            "mcp_jsonrpc_request",
            method=method,
            request_id=request_id,
            has_params=bool(params),
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.base_url,
                    json=jsonrpc_request,
                    headers=self._get_headers(),
                )

                self.logger.info(
                    "mcp_jsonrpc_response",
                    method=method,
                    status_code=response.status_code,
                )

                # Raise for HTTP errors
                response.raise_for_status()

                # Parse JSON-RPC response
                jsonrpc_response = response.json()

                # Check for JSON-RPC errors
                if "error" in jsonrpc_response:
                    error = jsonrpc_response["error"]
                    error_msg = f"JSON-RPC error {error.get('code')}: {error.get('message')}"
                    self.logger.error(
                        "mcp_jsonrpc_error",
                        method=method,
                        error_code=error.get("code"),
                        error_message=error.get("message"),
                    )
                    raise Exception(error_msg)

                # Return result
                result = jsonrpc_response.get("result")

                self.logger.info(
                    "mcp_jsonrpc_success",
                    method=method,
                    has_result=result is not None,
                )

                return result

        except httpx.TimeoutException as e:
            error_msg = f"MCP request timeout after {self.timeout}s: {method}"
            self.logger.error(
                "mcp_jsonrpc_timeout",
                method=method,
                timeout=self.timeout,
                error=str(e),
            )
            raise Exception(error_msg) from e

        except httpx.HTTPStatusError as e:
            error_msg = f"MCP HTTP error {e.response.status_code}: {method}"
            self.logger.error(
                "mcp_jsonrpc_http_error",
                method=method,
                status_code=e.response.status_code,
                error=str(e),
            )
            # Try to get error details from response
            try:
                error_details = e.response.json()
                error_msg = f"{error_msg} - {error_details}"
            except Exception:
                pass

            raise Exception(error_msg) from e

        except Exception as e:
            error_msg = f"MCP request failed: {method} - {str(e)}"
            self.logger.error(
                "mcp_jsonrpc_request_error",
                method=method,
                error=str(e),
            )
            raise Exception(error_msg) from e

    async def list_tools(self) -> list[dict[str, Any]]:
        """
        List available tools from MCP server.

        Returns:
            List of tool definitions

        Raises:
            Exception: If the request fails
        """
        self.logger.info("mcp_listing_tools")

        try:
            result = await self._send_jsonrpc_request(method="tools/list")

            tools = result.get("tools", []) if result else []

            self.logger.info(
                "mcp_tools_listed",
                num_tools=len(tools),
            )

            return tools

        except Exception as e:
            error_msg = f"Failed to list MCP tools: {str(e)}"
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
            Tool execution result

        Raises:
            Exception: If the request fails
        """
        self.logger.info(
            "mcp_calling_tool",
            tool_name=tool_name,
            args=list(arguments.keys()),
        )

        try:
            result = await self._send_jsonrpc_request(
                method="tools/call",
                params={
                    "name": tool_name,
                    "arguments": arguments,
                },
            )

            # Extract content from result
            content = result.get("content", []) if result else []
            is_error = result.get("isError", False) if result else False

            self.logger.info(
                "mcp_tool_called",
                tool_name=tool_name,
                is_error=is_error,
                has_content=bool(content),
            )

            return {
                "content": content,
                "isError": is_error,
                "_raw": result,
            }

        except Exception as e:
            error_msg = f"Failed to call MCP tool '{tool_name}': {str(e)}"
            self.logger.error(
                "mcp_call_tool_error",
                tool_name=tool_name,
                error=str(e),
            )
            raise Exception(error_msg) from e

    async def health_check(self) -> bool:
        """
        Check if MCP server is responsive.

        Returns:
            True if server responds, False otherwise
        """
        try:
            # Try to list tools as health check
            await self.list_tools()
            return True
        except Exception as e:
            self.logger.warning("mcp_health_check_failed", error=str(e))
            return False
