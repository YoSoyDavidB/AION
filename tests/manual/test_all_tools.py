"""
Test script for all tools including Web Search and Code Executor.
Tests both automatic tool selection and manual tool choice.
"""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.infrastructure.llm.openrouter_client import OpenRouterClient
from src.infrastructure.llm.llm_service import LLMService
from src.infrastructure.tools import (
    CalculatorTool,
    CodeExecutorTool,
    ToolRegistry,
    WebSearchTool,
)


async def test_tools():
    """Test all tools with various scenarios."""

    # Setup
    client = OpenRouterClient()
    registry = ToolRegistry()

    # Register all tools
    calculator = CalculatorTool()
    registry.register(calculator)

    web_search = WebSearchTool()
    registry.register(web_search)

    code_executor = CodeExecutorTool()
    registry.register(code_executor)

    llm_service = LLMService(client=client, tool_registry=registry)

    print("=" * 80)
    print("TESTING ALL TOOLS")
    print("=" * 80)

    # Test 1: Calculator Tool (auto mode)
    print("\n" + "=" * 80)
    print("TEST 1: Calculator Tool (auto mode)")
    print("=" * 80)
    messages = [
        {"role": "user", "content": "What is 156 * 78 + 234?"}
    ]

    try:
        response = await llm_service.chat_with_tools(
            messages=messages,
            max_tokens=500,
            tool_choice="auto"
        )

        answer = response["choices"][0]["message"]["content"]
        tools_used = response.get("tool_calls_history", [])

        print(f"\nQuestion: {messages[0]['content']}")
        print(f"Answer: {answer}")
        print(f"\nTools used: {len(tools_used)}")
        for i, tool_call in enumerate(tools_used, 1):
            print(f"\n  Tool {i}:")
            print(f"    Name: {tool_call.get('name')}")
            print(f"    Arguments: {tool_call.get('arguments')}")
            print(f"    Result: {tool_call.get('result')}")
    except Exception as e:
        print(f"ERROR: {e}")

    # Test 2: Web Search Tool (auto mode)
    print("\n" + "=" * 80)
    print("TEST 2: Web Search Tool (auto mode)")
    print("=" * 80)
    messages = [
        {"role": "user", "content": "What's the latest news about artificial intelligence in 2025?"}
    ]

    try:
        response = await llm_service.chat_with_tools(
            messages=messages,
            max_tokens=800,
            tool_choice="auto"
        )

        answer = response["choices"][0]["message"]["content"]
        tools_used = response.get("tool_calls_history", [])

        print(f"\nQuestion: {messages[0]['content']}")
        print(f"Answer: {answer}")
        print(f"\nTools used: {len(tools_used)}")
        for i, tool_call in enumerate(tools_used, 1):
            print(f"\n  Tool {i}:")
            print(f"    Name: {tool_call.get('name')}")
            print(f"    Arguments: {tool_call.get('arguments')}")
            result = tool_call.get('result', {})
            if isinstance(result, dict):
                print(f"    Results found: {result.get('results_count', 0)}")
                if result.get('results'):
                    print(f"    First result: {result['results'][0].get('title', 'N/A')}")
    except Exception as e:
        print(f"ERROR: {e}")

    # Test 3: Code Executor Tool (auto mode)
    print("\n" + "=" * 80)
    print("TEST 3: Code Executor Tool (auto mode)")
    print("=" * 80)
    messages = [
        {"role": "user", "content": "Generate the first 10 Fibonacci numbers using Python code."}
    ]

    try:
        response = await llm_service.chat_with_tools(
            messages=messages,
            max_tokens=800,
            tool_choice="auto"
        )

        answer = response["choices"][0]["message"]["content"]
        tools_used = response.get("tool_calls_history", [])

        print(f"\nQuestion: {messages[0]['content']}")
        print(f"Answer: {answer}")
        print(f"\nTools used: {len(tools_used)}")
        for i, tool_call in enumerate(tools_used, 1):
            print(f"\n  Tool {i}:")
            print(f"    Name: {tool_call.get('name')}")
            print(f"    Arguments: {tool_call.get('arguments')}")
            result = tool_call.get('result', {})
            if isinstance(result, dict):
                print(f"    Success: {result.get('success')}")
                if result.get('output'):
                    print(f"    Output: {result['output']}")
    except Exception as e:
        print(f"ERROR: {e}")

    # Test 4: Manual Tool Choice - Force Calculator
    print("\n" + "=" * 80)
    print("TEST 4: Manual Tool Choice - Force Calculator")
    print("=" * 80)
    messages = [
        {"role": "user", "content": "What is 25 + 17?"}
    ]

    try:
        response = await llm_service.chat_with_tools(
            messages=messages,
            max_tokens=500,
            tool_choice="calculator"  # Force calculator tool
        )

        answer = response["choices"][0]["message"]["content"]
        tools_used = response.get("tool_calls_history", [])

        print(f"\nQuestion: {messages[0]['content']}")
        print(f"Answer: {answer}")
        print(f"\nTools used: {len(tools_used)}")
        for i, tool_call in enumerate(tools_used, 1):
            print(f"\n  Tool {i}:")
            print(f"    Name: {tool_call.get('name')} (FORCED)")
            print(f"    Arguments: {tool_call.get('arguments')}")
            print(f"    Result: {tool_call.get('result')}")
    except Exception as e:
        print(f"ERROR: {e}")

    # Test 5: Manual Tool Choice - Force Web Search
    print("\n" + "=" * 80)
    print("TEST 5: Manual Tool Choice - Force Web Search")
    print("=" * 80)
    messages = [
        {"role": "user", "content": "Find information about Python programming language."}
    ]

    try:
        response = await llm_service.chat_with_tools(
            messages=messages,
            max_tokens=800,
            tool_choice="web_search"  # Force web search tool
        )

        answer = response["choices"][0]["message"]["content"]
        tools_used = response.get("tool_calls_history", [])

        print(f"\nQuestion: {messages[0]['content']}")
        print(f"Answer: {answer}")
        print(f"\nTools used: {len(tools_used)}")
        for i, tool_call in enumerate(tools_used, 1):
            print(f"\n  Tool {i}:")
            print(f"    Name: {tool_call.get('name')} (FORCED)")
            print(f"    Arguments: {tool_call.get('arguments')}")
            result = tool_call.get('result', {})
            if isinstance(result, dict):
                print(f"    Results found: {result.get('results_count', 0)}")
    except Exception as e:
        print(f"ERROR: {e}")

    # Test 6: Tool Choice None - Disable all tools
    print("\n" + "=" * 80)
    print("TEST 6: Tool Choice None - Disable Tools")
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
        print("Note: LLM should answer directly without using calculator")
    except Exception as e:
        print(f"ERROR: {e}")

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_tools())
