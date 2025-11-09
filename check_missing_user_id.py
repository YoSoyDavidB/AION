"""Check for points missing user_id."""
import asyncio
from src.infrastructure.vector_store.memory_repository_impl import QdrantMemoryRepository


async def check_points():
    """Check which points are missing user_id."""
    repo = QdrantMemoryRepository()

    try:
        # Scroll through all points
        all_points = []
        offset = None

        while True:
            results, next_offset = await repo.client.client.scroll(
                collection_name="memories",
                limit=100,
                with_vectors=False,
                offset=offset,
            )

            if not results:
                break

            all_points.extend(results)
            offset = next_offset

            if next_offset is None:
                break

        print(f"Total points: {len(all_points)}")

        # Find points missing user_id
        missing_user_id = []
        for point in all_points:
            if "user_id" not in point.payload:
                missing_user_id.append(point)

        print(f"Points missing user_id: {len(missing_user_id)}")

        if missing_user_id:
            print("\nFirst 5 points missing user_id:")
            for point in missing_user_id[:5]:
                print(f"  ID: {point.id}")
                print(f"  Payload keys: {list(point.payload.keys())}")
                print()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_points())
