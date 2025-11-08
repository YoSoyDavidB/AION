"""
Tool Registry for managing available tools.
"""

from typing import Any

from src.domain.entities.tool import BaseTool, ToolCall, ToolResult
from src.shared.logging import LoggerMixin


class ToolRegistry(LoggerMixin):
    """
    Registry for all available tools.

    Manages tool registration, discovery, and execution.
    """

    def __init__(self):
        """Initialize tool registry."""
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.

        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool
        self.logger.info("tool_registered", tool_name=tool.name)

    def unregister(self, tool_name: str) -> None:
        """
        Unregister a tool.

        Args:
            tool_name: Name of tool to unregister
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            self.logger.info("tool_unregistered", tool_name=tool_name)

    def get_tool(self, tool_name: str) -> BaseTool | None:
        """
        Get a tool by name.

        Args:
            tool_name: Name of tool to retrieve

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> list[BaseTool]:
        """
        Get all registered tools.

        Returns:
            List of all tools
        """
        return list(self._tools.values())

    def get_tools_definitions(self) -> list[dict[str, Any]]:
        """
        Get all tool definitions in OpenAI format.

        Returns:
            List of tool definitions for LLM
        """
        return [tool.to_openai_format() for tool in self._tools.values()]

    async def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """
        Execute a tool call.

        Args:
            tool_call: Tool call to execute

        Returns:
            Tool execution result
        """
        self.logger.info(
            "executing_tool_call",
            tool_name=tool_call.tool_name,
            tool_call_id=tool_call.tool_call_id,
        )

        tool = self.get_tool(tool_call.tool_name)

        if tool is None:
            self.logger.error("tool_not_found", tool_name=tool_call.tool_name)
            return ToolResult(
                tool_call_id=tool_call.tool_call_id,
                tool_name=tool_call.tool_name,
                success=False,
                result=None,
                error=f"Tool '{tool_call.tool_name}' not found",
            )

        try:
            # Execute tool with arguments
            result = await tool.execute(**tool_call.arguments)

            self.logger.info(
                "tool_call_success",
                tool_name=tool_call.tool_name,
                tool_call_id=tool_call.tool_call_id,
            )

            return ToolResult(
                tool_call_id=tool_call.tool_call_id,
                tool_name=tool_call.tool_name,
                success=True,
                result=result,
            )

        except Exception as e:
            self.logger.error(
                "tool_call_failed",
                tool_name=tool_call.tool_name,
                tool_call_id=tool_call.tool_call_id,
                error=str(e),
            )

            return ToolResult(
                tool_call_id=tool_call.tool_call_id,
                tool_name=tool_call.tool_name,
                success=False,
                result=None,
                error=str(e),
            )

    async def execute_multiple_tool_calls(
        self, tool_calls: list[ToolCall]
    ) -> list[ToolResult]:
        """
        Execute multiple tool calls.

        Args:
            tool_calls: List of tool calls to execute

        Returns:
            List of tool execution results in same order
        """
        self.logger.info(
            "executing_multiple_tool_calls", num_calls=len(tool_calls)
        )

        results = []
        for tool_call in tool_calls:
            result = await self.execute_tool_call(tool_call)
            results.append(result)

        return results
