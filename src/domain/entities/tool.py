"""
Tool domain entities for function calling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolParameter:
    """Defines a parameter for a tool."""

    name: str
    type: str  # "string", "number", "boolean", "object", "array"
    description: str
    required: bool = False
    enum: list[str] | None = None  # For restricted values


@dataclass
class ToolDefinition:
    """
    Defines a tool that can be called by the LLM.

    This follows the OpenRouter/OpenAI tool calling format.
    """

    name: str
    description: str
    parameters: list[ToolParameter]

    def to_openai_format(self) -> dict[str, Any]:
        """
        Convert to OpenAI/OpenRouter tool definition format.

        Returns:
            Dictionary with tool definition in OpenAI format
        """
        # Build parameters schema
        properties = {}
        required_params = []

        for param in self.parameters:
            param_schema = {
                "type": param.type,
                "description": param.description,
            }

            if param.enum:
                param_schema["enum"] = param.enum

            properties[param.name] = param_schema

            if param.required:
                required_params.append(param.name)

        parameters_schema = {
            "type": "object",
            "properties": properties,
        }

        if required_params:
            parameters_schema["required"] = required_params

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": parameters_schema,
            },
        }


@dataclass
class ToolCall:
    """Represents a tool call requested by the LLM."""

    tool_call_id: str
    tool_name: str
    arguments: dict[str, Any]


@dataclass
class ToolResult:
    """Result of a tool execution."""

    tool_call_id: str
    tool_name: str
    success: bool
    result: Any
    error: str | None = None

    def to_message_format(self) -> dict[str, Any]:
        """
        Convert to OpenRouter message format for tool results.

        Returns:
            Dictionary with tool result in message format
        """
        if self.success:
            content = str(self.result)
        else:
            content = f"Error: {self.error}"

        return {
            "role": "tool",
            "tool_call_id": self.tool_call_id,
            "content": content,
        }


class BaseTool(ABC):
    """
    Abstract base class for all tools.

    Tools are capabilities that the LLM can request to be executed.
    The tool defines what it does, what parameters it needs, and how to execute.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this tool does."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> list[ToolParameter]:
        """List of parameters this tool accepts."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """
        Execute the tool with provided arguments.

        Args:
            **kwargs: Tool arguments as keyword arguments

        Returns:
            Tool execution result

        Raises:
            Exception: If tool execution fails
        """
        pass

    def get_definition(self) -> ToolDefinition:
        """
        Get the tool definition.

        Returns:
            ToolDefinition with name, description, and parameters
        """
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )

    def to_openai_format(self) -> dict[str, Any]:
        """
        Get tool definition in OpenAI/OpenRouter format.

        Returns:
            Dictionary with tool definition
        """
        return self.get_definition().to_openai_format()
