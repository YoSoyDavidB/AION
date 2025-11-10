"""
Tools infrastructure for function calling.
"""

from src.infrastructure.tools.calculator_tool import CalculatorTool
from src.infrastructure.tools.code_executor_tool import CodeExecutorTool
from src.infrastructure.tools.tool_registry import ToolRegistry
from src.infrastructure.tools.web_search_tool import WebSearchTool
from src.infrastructure.tools.web_fetch_tool import WebFetchTool
from src.infrastructure.tools.weather_tool import WeatherTool

# KnowledgeBaseTool, CalendarTool, and EmailTool are not imported here to avoid circular dependencies
# Import them directly when needed:
# from src.infrastructure.tools.knowledge_base_tool import KnowledgeBaseTool
# from src.infrastructure.tools.calendar_tool import CalendarTool
# from src.infrastructure.tools.email_tool import EmailTool

__all__ = ["CalculatorTool", "CodeExecutorTool", "WebSearchTool", "WebFetchTool", "WeatherTool", "ToolRegistry"]
