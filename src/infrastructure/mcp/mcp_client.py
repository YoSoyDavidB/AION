"""
Generic MCP (Model Context Protocol) client for N8N integrations.
"""

from typing import Any

import httpx

from src.shared.logging import LoggerMixin


class MCPClient(LoggerMixin):
    """
    Generic client for communicating with MCP servers in N8N.

    Handles authentication, request formatting, and error handling
    for all MCP-based integrations.
    """

    def __init__(
        self,
        base_url: str,
        auth_header_name: str = "X-API-Key",
        auth_header_value: str | None = None,
        timeout: int = 30,
    ):
        """
        Initialize MCP client.

        Args:
            base_url: Base URL of the MCP server
            auth_header_name: Name of authentication header
            auth_header_value: Value for authentication header
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.auth_header_name = auth_header_name
        self.auth_header_value = auth_header_value
        self.timeout = timeout

        self.logger.info(
            "mcp_client_initialized",
            base_url=base_url,
            has_auth=bool(auth_header_value),
        )

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

    async def call_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        additional_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Call an MCP tool endpoint.

        Args:
            tool_name: Name of the tool to call
            parameters: Tool parameters
            additional_headers: Additional HTTP headers

        Returns:
            Tool execution result

        Raises:
            Exception: If the request fails
        """
        endpoint = f"{self.base_url}/tools/{tool_name}"

        self.logger.info(
            "mcp_tool_call_starting",
            tool_name=tool_name,
            endpoint=endpoint,
            params=list(parameters.keys()),
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint,
                    json=parameters,
                    headers=self._get_headers(additional_headers),
                )

                # Log response status
                self.logger.info(
                    "mcp_tool_call_response",
                    tool_name=tool_name,
                    status_code=response.status_code,
                )

                # Raise for HTTP errors
                response.raise_for_status()

                # Parse and return result
                result = response.json()

                self.logger.info(
                    "mcp_tool_call_success",
                    tool_name=tool_name,
                    result_keys=list(result.keys()) if isinstance(result, dict) else None,
                )

                return result

        except httpx.TimeoutException as e:
            error_msg = f"MCP call timeout after {self.timeout}s: {tool_name}"
            self.logger.error(
                "mcp_tool_call_timeout",
                tool_name=tool_name,
                timeout=self.timeout,
                error=str(e),
            )
            raise Exception(error_msg) from e

        except httpx.HTTPStatusError as e:
            error_msg = f"MCP HTTP error {e.response.status_code}: {tool_name}"
            self.logger.error(
                "mcp_tool_call_http_error",
                tool_name=tool_name,
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
            error_msg = f"MCP call failed: {tool_name} - {str(e)}"
            self.logger.error(
                "mcp_tool_call_error",
                tool_name=tool_name,
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
        endpoint = f"{self.base_url}/tools"

        self.logger.info("mcp_list_tools_starting", endpoint=endpoint)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    endpoint,
                    headers=self._get_headers(),
                )

                response.raise_for_status()
                tools = response.json()

                self.logger.info(
                    "mcp_list_tools_success",
                    num_tools=len(tools) if isinstance(tools, list) else 0,
                )

                return tools if isinstance(tools, list) else []

        except Exception as e:
            error_msg = f"Failed to list MCP tools: {str(e)}"
            self.logger.error("mcp_list_tools_error", error=str(e))
            raise Exception(error_msg) from e

    async def health_check(self) -> bool:
        """
        Check if MCP server is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            endpoint = f"{self.base_url}/health"

            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    endpoint,
                    headers=self._get_headers(),
                )

                is_healthy = response.status_code == 200

                self.logger.info(
                    "mcp_health_check",
                    is_healthy=is_healthy,
                    status_code=response.status_code,
                )

                return is_healthy

        except Exception as e:
            self.logger.warning("mcp_health_check_failed", error=str(e))
            return False
