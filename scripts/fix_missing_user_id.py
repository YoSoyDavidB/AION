"""Fix points missing user_id by adding default value."""
import asyncio
from src.infrastructure.vector_store.memory_repository_impl import QdrantMemoryRepository


async def fix_missing_user_id():
    """Add user_id to points that are missing it."""
    repo = QdrantMemoryRepository()
    default_user_id = "david"  # Default user for this system

    try:
        # Scroll through all points
        all_points = []
        offset = None

        print("Fetching all points...")
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

        # Find and fix points missing user_id
        missing_user_id = []
        for point in all_points:
            if "user_id" not in point.payload:
                missing_user_id.append(point)

        print(f"Points missing user_id: {len(missing_user_id)}")

        if missing_user_id:
            print(f"\nUpdating {len(missing_user_id)} points with user_id='{default_user_id}'...")

            for i, point in enumerate(missing_user_id):
                # Update the payload with user_id
                updated_payload = dict(point.payload)
                updated_payload["user_id"] = default_user_id

                # Update the point in Qdrant
                await repo.client.client.set_payload(
                    collection_name="memories",
                    payload={"user_id": default_user_id},
                    points=[point.id],
                )

                if (i + 1) % 5 == 0:
                    print(f"  Updated {i + 1}/{len(missing_user_id)} points")

            print(f"✓ Successfully updated {len(missing_user_id)} points!")

            # Verify
            print("\nVerifying fix...")
            results, _ = await repo.client.client.scroll(
                collection_name="memories",
                limit=5,
                with_vectors=False,
            )

            still_missing = sum(1 for p in results if "user_id" not in p.payload)
            print(f"Points still missing user_id in sample: {still_missing}")

        else:
            print("All points already have user_id!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(fix_missing_user_id())
