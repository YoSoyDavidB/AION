"""
Simple test for Calculator Tool function calling.
"""

import asyncio

from src.infrastructure.llm.llm_service import LLMService
from src.infrastructure.tools import CalculatorTool, ToolRegistry


async def main():
    """Test calculator tool with function calling."""
    print("="  * 60)
    print("CALCULATOR TOOL - FUNCTION CALLING TEST")
    print("=" * 60)

    # Initialize tool registry
    tool_registry = ToolRegistry()

    # Register calculator tool
    calculator = CalculatorTool()
    tool_registry.register(calculator)

    print(f"\n✓ Registered {len(tool_registry.list_tools())} tool(s)")
    print(f"  - {calculator.name}: {calculator.description[:80]}...")

    # Initialize LLM service with tool registry
    llm_service = LLMService(tool_registry=tool_registry)

    # Test case 1: Simple calculation
    print("\n" + "-" * 60)
    print("Test 1: Simple calculation")
    print("-" * 60)

    messages = [
        {
            "role": "user",
            "content": "What is 25 * 4 + 10? Please calculate it for me.",
        }
    ]

    try:
        response = await llm_service.chat_with_tools(messages, max_tokens=500)

        print(f"\n✓ Tool calling completed!")
        print(f"  - Iterations: {response.get('iterations', 0)}")
        print(f"  - Tool calls: {len(response.get('tool_calls_history', []))}")

        # Print tool calls history
        if response.get("tool_calls_history"):
            print("\n  Tool calls executed:")
            for i, tc in enumerate(response["tool_calls_history"], 1):
                print(f"    {i}. {tc['tool_name']}({tc['arguments']})")
                print(f"       → Result: {tc['result']}")
                print(f"       → Success: {tc['success']}")

        # Print final response
        final_message = response["choices"][0]["message"]["content"]
        print(f"\n  Final response:\n    {final_message}\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()

    # Test case 2: Complex calculation
    print("\n" + "-" * 60)
    print("Test 2: Complex calculation with functions")
    print("-" * 60)

    messages = [
        {
            "role": "user",
            "content": "Calculate the square root of 144 plus 10 to the power of 2",
        }
    ]

    try:
        response = await llm_service.chat_with_tools(messages, max_tokens=500)

        print(f"\n✓ Tool calling completed!")
        print(f"  - Iterations: {response.get('iterations', 0)}")
        print(f"  - Tool calls: {len(response.get('tool_calls_history', []))}")

        # Print tool calls history
        if response.get("tool_calls_history"):
            print("\n  Tool calls executed:")
            for i, tc in enumerate(response["tool_calls_history"], 1):
                print(f"    {i}. {tc['tool_name']}({tc['arguments']})")
                print(f"       → Result: {tc['result']}")

        # Print final response
        final_message = response["choices"][0]["message"]["content"]
        print(f"\n  Final response:\n    {final_message}\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()

    # Clean up
    await llm_service.close()

    print("=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
