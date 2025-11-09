"""
Test script for function calling implementation.
"""

import asyncio

from src.application.use_cases.memory_use_cases import SearchMemoriesUseCase
from src.infrastructure.embeddings.embedding_service import EmbeddingService
from src.infrastructure.llm.llm_service import LLMService
from src.infrastructure.tools import (
    CalculatorTool,
    KnowledgeBaseTool,
    ToolRegistry,
)
from src.infrastructure.vector_store.document_repository_impl import (
    DocumentRepositoryImpl,
)
from src.infrastructure.vector_store.memory_repository_impl import (
    MemoryRepositoryImpl,
)
from src.infrastructure.vector_store.qdrant_client import QdrantClientImpl


async def test_calculator_tool():
    """Test calculator tool."""
    print("\n=== Testing Calculator Tool ===")

    # Initialize tool registry
    tool_registry = ToolRegistry()

    # Register calculator tool
    calculator = CalculatorTool()
    tool_registry.register(calculator)

    # Initialize LLM service with tool registry
    llm_service = LLMService(tool_registry=tool_registry)

    # Test messages
    messages = [
        {
            "role": "user",
            "content": "What is the result of 25 * 4 + 10? Please calculate it.",
        }
    ]

    try:
        response = await llm_service.chat_with_tools(messages)

        print(f"\n✓ Tool calling completed in {response.get('iterations', 0)} iterations")
        print(f"✓ Number of tool calls: {len(response.get('tool_calls_history', []))}")

        # Print tool calls history
        if response.get("tool_calls_history"):
            print("\nTool calls:")
            for i, tc in enumerate(response["tool_calls_history"], 1):
                print(f"  {i}. {tc['tool_name']}({tc['arguments']})")
                print(f"     Result: {tc['result']}")
                print(f"     Success: {tc['success']}")

        # Print final response
        final_message = response["choices"][0]["message"]["content"]
        print(f"\nFinal response:\n{final_message}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await llm_service.close()


async def test_knowledge_base_tool():
    """Test knowledge base tool."""
    print("\n=== Testing Knowledge Base Tool ===")

    # Initialize dependencies
    embedding_service = EmbeddingService()
    qdrant_client = QdrantClientImpl()

    # Initialize repositories
    memory_repo = MemoryRepositoryImpl(
        qdrant_client=qdrant_client, embedding_service=embedding_service
    )
    document_repo = DocumentRepositoryImpl(
        qdrant_client=qdrant_client, embedding_service=embedding_service
    )

    # Initialize search use case
    search_memories_use_case = SearchMemoriesUseCase(memory_repo=memory_repo)

    # Initialize tool registry
    tool_registry = ToolRegistry()

    # Register knowledge base tool
    kb_tool = KnowledgeBaseTool(
        search_memories_use_case=search_memories_use_case,
        document_repo=document_repo,
    )
    tool_registry.register(kb_tool)

    # Initialize LLM service with tool registry
    llm_service = LLMService(tool_registry=tool_registry)

    # Test messages
    messages = [
        {
            "role": "user",
            "content": "Search my knowledge base for information about Colombia and tell me what you find.",
        }
    ]

    try:
        response = await llm_service.chat_with_tools(
            messages, temperature=0.7, max_tokens=500
        )

        print(f"\n✓ Tool calling completed in {response.get('iterations', 0)} iterations")
        print(f"✓ Number of tool calls: {len(response.get('tool_calls_history', []))}")

        # Print tool calls history
        if response.get("tool_calls_history"):
            print("\nTool calls:")
            for i, tc in enumerate(response["tool_calls_history"], 1):
                print(f"  {i}. {tc['tool_name']}")
                print(f"     Arguments: {tc['arguments']}")
                if tc["success"]:
                    result = tc["result"]
                    print(
                        f"     Found: {result.get('total_results', 0)} results ({len(result.get('memories', []))} memories, {len(result.get('documents', []))} documents)"
                    )
                else:
                    print(f"     Error: {tc['error']}")

        # Print final response
        final_message = response["choices"][0]["message"]["content"]
        print(f"\nFinal response:\n{final_message}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await llm_service.close()
        await qdrant_client.close()


async def test_both_tools():
    """Test both tools together."""
    print("\n=== Testing Both Tools Together ===")

    # Initialize dependencies
    embedding_service = EmbeddingService()
    qdrant_client = QdrantClientImpl()

    # Initialize repositories
    memory_repo = MemoryRepositoryImpl(
        qdrant_client=qdrant_client, embedding_service=embedding_service
    )
    document_repo = DocumentRepositoryImpl(
        qdrant_client=qdrant_client, embedding_service=embedding_service
    )

    # Initialize search use case
    search_memories_use_case = SearchMemoriesUseCase(memory_repo=memory_repo)

    # Initialize tool registry
    tool_registry = ToolRegistry()

    # Register both tools
    calculator = CalculatorTool()
    kb_tool = KnowledgeBaseTool(
        search_memories_use_case=search_memories_use_case,
        document_repo=document_repo,
    )

    tool_registry.register(calculator)
    tool_registry.register(kb_tool)

    # Initialize LLM service with tool registry
    llm_service = LLMService(tool_registry=tool_registry)

    # Test messages - complex query that might use both tools
    messages = [
        {
            "role": "user",
            "content": "I was born in 1986. How many years ago was that? Also, search my knowledge base to see if there's any information about where I was born.",
        }
    ]

    try:
        import datetime

        current_year = datetime.datetime.now().year
        print(f"\n(Current year: {current_year})")

        response = await llm_service.chat_with_tools(
            messages, temperature=0.7, max_tokens=800
        )

        print(f"\n✓ Tool calling completed in {response.get('iterations', 0)} iterations")
        print(f"✓ Number of tool calls: {len(response.get('tool_calls_history', []))}")

        # Print tool calls history
        if response.get("tool_calls_history"):
            print("\nTool calls:")
            for i, tc in enumerate(response["tool_calls_history"], 1):
                print(f"  {i}. {tc['tool_name']}")
                print(f"     Arguments: {tc['arguments']}")
                print(f"     Result: {str(tc['result'])[:200]}...")
                print(f"     Success: {tc['success']}")

        # Print final response
        final_message = response["choices"][0]["message"]["content"]
        print(f"\nFinal response:\n{final_message}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await llm_service.close()
        await qdrant_client.close()


async def main():
    """Run all tests."""
    print("=" * 60)
    print("FUNCTION CALLING TESTS")
    print("=" * 60)

    await test_calculator_tool()
    await test_knowledge_base_tool()
    await test_both_tools()

    print("\n" + "=" * 60)
    print("TESTS COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
