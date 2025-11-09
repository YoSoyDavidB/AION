"""Test memory scroll from Qdrant."""
import asyncio
from src.infrastructure.vector_store.memory_repository_impl import QdrantMemoryRepository


async def test_scroll():
    """Test scrolling memories from Qdrant."""
    repo = QdrantMemoryRepository()

    # Get collection info
    try:
        from qdrant_client import models

        # Try to scroll and print what we get
        results, next_offset = await repo.client.client.scroll(
            collection_name="memories",
            limit=2,
            with_vectors=True,
        )

        print(f"Number of results: {len(results)}")
        print(f"Next offset: {next_offset}")

        if results:
            first_point = results[0]
            print(f"\nFirst point ID: {first_point.id}")
            print(f"First point payload keys: {first_point.payload.keys() if first_point.payload else 'None'}")
            print(f"First point vector type: {type(first_point.vector)}")
            print(f"First point vector length: {len(first_point.vector) if first_point.vector else 'None'}")

            if first_point.payload:
                print(f"\nFirst point payload:")
                for key, value in first_point.payload.items():
                    print(f"  {key}: {value}")

        # Now try get_recent
        print("\n\n=== Testing get_recent ===")
        memories = await repo.get_recent(limit=2)
        print(f"Got {len(memories)} memories")

        if memories:
            first_memory = memories[0]
            print(f"\nFirst memory:")
            print(f"  ID: {first_memory.memory_id}")
            print(f"  User ID: {first_memory.user_id}")
            print(f"  Text: {first_memory.short_text[:50]}...")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_scroll())
