"""
Tools infrastructure for function calling.
"""

from src.infrastructure.tools.calculator_tool import CalculatorTool
from src.infrastructure.tools.tool_registry import ToolRegistry

# KnowledgeBaseTool is not imported here to avoid circular dependencies
# Import it directly when needed: from src.infrastructure.tools.knowledge_base_tool import KnowledgeBaseTool

__all__ = ["CalculatorTool", "ToolRegistry"]
