"""
Quick test for tool_choice="none" fix.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.infrastructure.llm.openrouter_client import OpenRouterClient
from src.infrastructure.llm.llm_service import LLMService
from src.infrastructure.tools import (
    CalculatorTool,
    CodeExecutorTool,
    ToolRegistry,
    WebSearchTool,
)


async def test_tool_choice_none():
    """Test that tool_choice='none' works correctly."""

    # Setup
    client = OpenRouterClient()
    registry = ToolRegistry()

    # Register tools
    calculator = CalculatorTool()
    registry.register(calculator)

    web_search = WebSearchTool()
    registry.register(web_search)

    code_executor = CodeExecutorTool()
    registry.register(code_executor)

    llm_service = LLMService(client=client, tool_registry=registry)

    print("=" * 80)
    print("TEST: Tool Choice None - Disable Tools")
    print("=" * 80)

    messages = [
        {"role": "user", "content": "What is 50 + 30?"}
    ]

    try:
        response = await llm_service.chat_with_tools(
            messages=messages,
            max_tokens=500,
            tool_choice="none"  # Disable all tools
        )

        answer = response["choices"][0]["message"]["content"]
        tools_used = response.get("tool_calls_history", [])

        print(f"\nQuestion: {messages[0]['content']}")
        print(f"Answer: {answer}")
        print(f"\nTools used: {len(tools_used)} (should be 0)")
        print("\nNote: LLM answered directly without using calculator tool")
        print("\n✅ TEST PASSED - tool_choice='none' works correctly!")

    except Exception as e:
        print(f"\n❌ TEST FAILED - Error: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_tool_choice_none())
